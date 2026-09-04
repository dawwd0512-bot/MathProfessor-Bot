import re
import os
import traceback
import runpy
import subprocess
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from core.ai.gemini import ask_gemini
from core.agent_v2 import AgentV2
from core.ai.math_engine import solve_math, format_result
from core.memory.conversation import conversation_memory
from core.memory.persistent import persistent_memory
from core.files.manager import process_file
from core.rag.rag_manager import RAGManager
from core.rag.book_summary import summarize_book
from core.rag.persistent import persistent_rag
from core.document_intelligence.bridge import document_bridge
from core.vision.image import analyze_image
from core.voice.tts import text_to_speech
from core.pdf_translation.translator import translate_pdf
from core.video_generation.video_request import build_video_plan
from core.video_generation.plan_adapter import plan_text_to_sequence
from core.video_generation.video_generator import (
    create_scene,
    create_video_from_scenes,
)


load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

BASE_DIR = Path.home() / "MathProfessor-Bot"

WHISPER_BIN = (
    BASE_DIR
    / "third_party"
    / "whisper.cpp"
    / "build"
    / "bin"
    / "whisper-cli"
)

WHISPER_MODEL = (
    BASE_DIR
    / "third_party"
    / "whisper.cpp"
    / "models"
    / "ggml-tiny-q5_1.bin"
)

DATA_DIR = BASE_DIR / "data"



def is_video_generation_request(text: str) -> bool:
    """
    يكتشف طلبات إنشاء الفيديو حتى لا يتم إرسالها
    إلى مساعد الرياضيات.
    """

    text_lower = text.strip().lower()

    video_words = [
        "اعمل لي فيديو",
        "اعمل فيديو",
        "اصنع لي فيديو",
        "اصنع فيديو",
        "أنشئ لي فيديو",
        "أنشئ فيديو",
        "انشئ لي فيديو",
        "انشئ فيديو",
        "سوي فيديو",
        "سويلي فيديو",
        "سوّي فيديو",
        "سوّيلي فيديو",
        "فيديو سينمائي",
        "فيديو وثائقي",
        "فيلم",
        "اصنع فيلم",
        "اعمل فيلم",
        "أنشئ فيلم",
        "انشئ فيلم",
        "create a video",
        "make a video",
        "generate a video",
        "cinematic video",
        "make a film",
    ]

    return any(
        word in text_lower
        for word in video_words
    )


# ============================================================
# HELPERS
# ============================================================

async def send_long_message(update, text):
    if not text:
        text = "❌ لم يتم الحصول على نتيجة."

    max_length = 4000

    for i in range(0, len(text), max_length):
        await update.message.reply_text(
            text[i:i + max_length]
        )


def run_command(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + result.stderr[-5000:]
        )

    return result.stdout, result.stderr


def extract_audio(input_file, output_wav):
    output_wav.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_file),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]

    run_command(command)


def transcribe_with_whisper(wav_file):
    if not WHISPER_BIN.exists():
        raise FileNotFoundError(
            f"Whisper غير موجود:\n{WHISPER_BIN}"
        )

    if not WHISPER_MODEL.exists():
        raise FileNotFoundError(
            f"موديل Whisper غير موجود:\n{WHISPER_MODEL}"
        )

    command = [
        str(WHISPER_BIN),
        "-m",
        str(WHISPER_MODEL),
        "-f",
        str(wav_file),
        "-l",
        "auto",
        "-nt",
    ]

    stdout, stderr = run_command(command)

    # whisper.cpp قد يضع النص في stdout أو stderr
    combined = stdout + "\n" + stderr

    lines = []

    for line in combined.splitlines():
        line = line.strip()

        if not line:
            continue

        # تجاهل رسائل التشغيل والتشخيص
        ignored = (
            "whisper_",
            "system_info:",
            "main:",
            "read_audio_data:",
            "processing",
            "ggml_",
        )

        if line.startswith(ignored):
            continue

        # تجاهل معلومات النموذج والأداء
        if (
            "compute buffer" in line
            or "model size" in line
            or "model load" in line
            or "load time" in line
            or "encode time" in line
            or "decode time" in line
            or "total time" in line
            or "sample time" in line
            or "batchd time" in line
            or "prompt time" in line
        ):
            continue

        # إزالة timestamps إن وجدت
        if line.startswith("[") and "]" in line:
            after = line.split("]", 1)[1].strip()

            if after:
                lines.append(after)

            continue

        # أي نص فعلي متبقٍ
        if line:
            lines.append(line)

    text = "\n".join(lines).strip()

    if not text:
        raise RuntimeError(
            "Whisper لم يُرجع نصًا.\n\n"
            "STDOUT:\n"
            + stdout[-2000:]
            + "\n\nSTDERR:\n"
            + stderr[-3000:]
        )

    return text


async def transcribe_audio_file(audio_file):
    wav_file = (
        DATA_DIR
        / "voice_test"
        / f"converted_{audio_file.stem}.wav"
    )

    await asyncio.to_thread(
        extract_audio,
        audio_file,
        wav_file
    )

    text = await asyncio.to_thread(
        transcribe_with_whisper,
        wav_file
    )

    return text


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎓 أهلاً بك في MathProfessor-Bot\n\n"
        "أنا مساعدك الذكي في الرياضيات.\n\n"
        "📚 أرسل سؤالاً رياضياً\n"
        "🖼️ أرسل صورة لمسألة\n"
        "📄 أرسل ملفاً\n"
        "🎤 أرسل تسجيل صوتي\n"
        "🎥 أرسل فيديو لمحاضرة\n\n"
        "وسأحلل المحتوى وأساعدك."
    )


# ============================================================
# PRONUNCIATION / TTS
# ============================================================

async def handle_pronunciation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        text = update.message.text.strip()

        if not text.startswith("/pronounce"):
            return

        word = text.replace(
            "/pronounce",
            "",
            1
        ).strip()

        if not word:
            await update.message.reply_text(
                "🔊 اكتب الكلمة بعد الأمر.\n\n"
                "مثال:\n"
                "/pronounce derivative"
            )
            return

        await update.message.reply_text(
            "🔊 جاري تجهيز النطق..."
        )

        audio_dir = DATA_DIR / "audio"

        audio_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        audio_path = (
            audio_dir
            / f"{update.effective_user.id}_pronunciation.mp3"
        )

        await text_to_speech(
            word,
            str(audio_path)
        )

        with open(audio_path, "rb") as audio:
            await update.message.reply_audio(
                audio=audio,
                title=f"Pronunciation: {word}"
            )

    except Exception as e:
        traceback.print_exc()

        await update.message.reply_text(
            f"❌ حدث خطأ أثناء إنشاء النطق:\n{e}"
        )


# ============================================================
# DOCUMENTS
# ============================================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        document = update.message.document

        filename = document.file_name or "document"

        await update.message.reply_text(
            "📄 جاري تحميل الملف..."
        )

        file = await document.get_file()

        upload_dir = DATA_DIR / "uploads"
        upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path = (
            upload_dir
            / f"{user_id}_{filename}"
        )

        await file.download_to_drive(
            custom_path=str(file_path),
            read_timeout=300,
            write_timeout=300,
            connect_timeout=60,
            pool_timeout=300,
        )

        # ====================================================
        # PDF: LOAD INTO RAG FIRST
        # ====================================================

        if file_path.suffix.lower() == ".pdf":

            await update.message.reply_text(
                "📚 تم استلام ملف PDF.\n"
                "🧠 جاري استخراج محتواه وتجهيزه للبحث..."
            )

            result = process_file(
                str(file_path),
                user_id
            )

            if result["status"] != "success":

                await update.message.reply_text(
                    f"❌ تعذر تحليل ملف PDF:\n"
                    f"{result.get('message', 'خطأ غير معروف')}"
                )

                return

            # ------------------------------------------------
            # تنظيف RAG السابق
            # ------------------------------------------------

            context.user_data.pop(
                "rag",
                None
            )

            context.user_data.pop(
                "current_file",
                None
            )

            # ------------------------------------------------
            # تحميل PDF في RAG
            # ------------------------------------------------

            rag = RAGManager()

            rag.load_document(
                user_id,
                result["content"],
                filename=filename,
            )

            context.user_data["rag"] = rag

            # ------------------------------------------------
            # OFFICIAL PDF TABLE OF CONTENTS
            # إضافة الفهرس الرسمي إلى أول صفحة من الملف
            # ------------------------------------------------
            try:
                official_pdf = add_official_toc_to_pdf(
                    str(file_path),
                    user_id,
                )

                if official_pdf:
                    file_path = Path(official_pdf)
                    result["path"] = str(file_path)

                    print(
                        "📚 Official TOC integrated:",
                        file_path,
                    )

            except Exception as toc_error:
                print(
                    "⚠️ Official TOC warning:",
                    repr(toc_error),
                )

            context.user_data["current_file"] = result

            # ------------------------------------------------
            # حفظه بشكل دائم
            # ------------------------------------------------

            persistent_rag.save_document(
                user_id,
                result["content"],
                {
                    "type": result.get("type"),
                    "path": result.get("path"),
                    "filename": filename,
                }
            )

            print(
                "📚 PDF loaded into RAG:",
                filename
            )

            # ------------------------------------------------
            # عرض قائمة العمليات بعد تجهيز الملف
            # ------------------------------------------------

            await update.message.reply_text(
                "✅ تم استلام الملف وتحليله وتجهيزه للبحث.\n\n"
                "📚 صار بإمكانك الآن تسألني عن الكتاب بالطريقة اللي تناسبك.\n\n"
                "💬 مش لازم تختار رقم — احكيلي طلبك بالعامية أو بالفصحى، وأنا أفهم المطلوب.\n\n"
                "مثلاً:\n"
                "• اشرحلي درس 2\n"
                "• هاتلي فهرس الكتاب\n"
                "• وين درس الاشتقاق؟\n"
                "• قسملي الكتاب لدروس واشرحهم\n"
                "• طلعلي القوانين والأمثلة\n"
                "• اعمللي خريطة ذهنية للدرس الثالث\n"
                "• حللي هذا الفصل\n"
                "• ترجملي الكتاب\n"
                "• حللي الكتاب بالكامل\n\n"
                "💡 اسأل مباشرة عن أي شيء داخل الكتاب."
            )

            # حفظ آخر PDF
            context.user_data["pending_pdf"] = str(file_path)

            return

        # ====================================================
        # OTHER FILES
        # ====================================================

        await update.message.reply_text(
            "📚 جاري تحليل الملف..."
        )

        result = process_file(
            str(file_path),
            user_id
        )

        if result["status"] == "success":

            context.user_data.pop(
                "rag",
                None
            )

            context.user_data.pop(
                "current_file",
                None
            )

            rag = RAGManager()

            rag.load_document(
                user_id,
                result["content"],
                filename=filename,
            )

            context.user_data["rag"] = rag
            context.user_data["current_file"] = result

            persistent_rag.save_document(
                user_id,
                result["content"],
                {
                    "type": result.get("type"),
                    "path": result.get("path"),
                    "filename": filename,
                }
            )

            await update.message.reply_text(
                "✅ تم استلام الملف وتحليله.\n\n"
                "الآن يمكنك طرح أسئلة عنه."
            )

        else:
            await update.message.reply_text(
                f"❌ {result['message']}"
            )

    except Exception as e:
        traceback.print_exc()

        await update.message.reply_text(
            f"❌ خطأ في الملف:\n{type(e).__name__}\n{e}"
        )



# ============================================================
# PDF ACTION MENU HANDLER
# ============================================================

async def handle_pdf_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = (update.message.text or "").strip()

    # لا نتدخل برسائل البوت العادية
    # إلا إذا كان هناك PDF بانتظار اختيار المستخدم.
    if not context.user_data.get("pending_pdf"):
        return

    if choice not in {"1", "2", "3", "4", "5"}:
        return

    pdf_path = context.user_data.get("pending_pdf")

    if not pdf_path or not Path(pdf_path).exists():
        await update.message.reply_text(
            "❌ لم أجد ملف PDF محفوظًا. أرسل الملف من جديد."
        )
        return

    try:
        if choice == "1":
            await update.message.reply_text(
                "🌍 جاري ترجمة الملف..."
            )

            translated = await asyncio.to_thread(
                translate_pdf,
                pdf_path
            )

            if translated and Path(translated).exists():
                with open(translated, "rb") as f:
                    await update.message.reply_document(
                        document=f,
                        filename=Path(translated).name,
                        caption="🇦🇪 تمت ترجمة الملف."
                    )
            else:
                await update.message.reply_text(
                    "❌ لم يتم إنشاء ملف الترجمة."
                )

        elif choice == "2":
            await update.message.reply_text(
                "📚 جاري تقسيم الكتاب إلى دروس وشرحها..."
            )

            await asyncio.to_thread(
                runpy.run_module,
                "core.book_intelligence.export_sections",
                run_name="__main__"
            )

            await update.message.reply_text(
                "✅ تم تقسيم الكتاب وإخراج الأقسام."
            )

        elif choice == "3":
            await update.message.reply_text(
                "🧠 جاري تجهيز الدروس والشرح والخرائط والرسومات...\n"
                "⏳ انتظر قليلًا."
            )

            await asyncio.to_thread(
                runpy.run_module,
                "core.book_intelligence.export_sections",
                run_name="__main__"
            )

            await update.message.reply_text(
                "✅ تم تجهيز المحتوى.\n"
                "📤 جاري إرسال الدروس والصور..."
            )

            sections_dir = DATA_DIR / "final_sections"
            image_dir = DATA_DIR / "generated_images"

            files = sorted(
                sections_dir.glob("section_*.md")
            )

            sent_files = 0
            sent_images = 0

            # إرسال ملفات الدروس
            for section_file in files:
                try:
                    with open(section_file, "rb") as f:
                        await update.message.reply_document(
                            document=f,
                            filename=section_file.name,
                            caption="📚 درس مشروح"
                        )
                    sent_files += 1
                except Exception as e:
                    print("⚠️ إرسال القسم:", e)

            # تحويل SVG إلى PNG وإرسالها كصور فعلية
            try:
                import cairosvg

                images = sorted(
                    image_dir.glob("section_*.svg")
                )

                for svg in images:
                    try:
                        png = svg.with_suffix(".png")

                        cairosvg.svg2png(
                            url=str(svg),
                            write_to=str(png),
                            output_width=1200
                        )

                        if png.exists():
                            with open(png, "rb") as f:
                                await update.message.reply_photo(
                                    photo=f,
                                    caption=f"🖼️ {svg.stem}"
                                )

                            sent_images += 1

                    except Exception as e:
                        print(
                            f"⚠️ تعذر تحويل/إرسال {svg.name}:",
                            e
                        )

            except Exception as e:
                print("⚠️ CairoSVG:", e)

            await update.message.reply_text(
                "🎉 اكتملت العملية!\n\n"
                f"📚 الدروس المرسلة: {sent_files}\n"
                f"🖼️ الصور المرسلة: {sent_images}\n\n"
                "🧠 تم تضمين الخرائط الذهنية والرسومات."
            )

        elif choice == "4":
            await update.message.reply_text(
                "📐 جاري استخراج القوانين والأمثلة..."
            )

            await asyncio.to_thread(
                runpy.run_module,
                "core.book_intelligence.run_analysis",
                run_name="__main__"
            )

            await update.message.reply_text(
                "✅ تم استخراج القوانين والأمثلة."
            )

        elif choice == "5":
            await update.message.reply_text(
                "🔬 جاري تحليل الكتاب بالكامل..."
            )

            await asyncio.to_thread(
                runpy.run_module,
                "core.book_intelligence.run_analysis",
                run_name="__main__"
            )

            await asyncio.to_thread(
                runpy.run_module,
                "core.book_intelligence.export_sections",
                run_name="__main__"
            )

            await update.message.reply_text(
                "🎉 اكتمل تحليل الكتاب وإخراج الأقسام."
            )

    except Exception as e:
        traceback.print_exc()

        await update.message.reply_text(
            f"❌ حدث خطأ:\n{type(e).__name__}: {e}"
        )

    finally:
        context.user_data.pop("pending_pdf", None)


# ============================================================
# IMAGES
# ============================================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        await update.message.reply_text(
            "🖼️ جاري تحليل الصورة..."
        )

        photo = update.message.photo[-1]

        file = await photo.get_file()

        image_dir = DATA_DIR / "images"
        image_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        image_path = (
            image_dir
            / f"{user_id}_{photo.file_unique_id}.jpg"
        )

        await file.download_to_drive(
            custom_path=str(image_path),
            read_timeout=120,
            write_timeout=120,
            connect_timeout=60,
            pool_timeout=120,
        )

        caption = update.message.caption

        # ----------------------------------------------------
        # حفظ آخر صورة للمستخدم
        # حتى يستطيع أن يقول لاحقًا:
        # "حل الباقي"
        # "حل 3 و4"
        # "كمل"
        # ----------------------------------------------------

        context.user_data["last_image_path"] = str(image_path)
        context.user_data["last_image_caption"] = caption or ""

        if caption:
            prompt = (
                "حل جميع الأسئلة الموجودة في الصورة، "
                "وليس سؤالًا واحدًا فقط.\n\n"
                "لكل سؤال:\n"
                "1. اكتب رقم السؤال.\n"
                "2. اكتب خطوات الحل.\n"
                "3. اذكر القانون المستخدم.\n"
                "4. اذكر الإجابة النهائية.\n\n"
                "راجع الصورة كاملة قبل الإجابة، "
                "ولا تتخط أي سؤال ظاهر فيها.\n\n"
                f"طلب المستخدم:\n{caption}"
            )
        else:
            prompt = (
                "حل جميع الأسئلة والتمارين الموجودة في الصورة.\n\n"
                "لكل سؤال:\n"
                "1. اكتب رقم السؤال.\n"
                "2. حل السؤال خطوة بخطوة.\n"
                "3. اذكر القانون المستخدم.\n"
                "4. اذكر الإجابة النهائية.\n\n"
                "راجع الصورة كاملة ولا تتوقف بعد أول سؤال."
            )

        answer = await asyncio.to_thread(
            analyze_image,
            str(image_path),
            prompt
        )

        conversation_memory.add(
            user_id,
            "user",
            caption or "[صورة]"
        )

        conversation_memory.add(
            user_id,
            "assistant",
            answer
        )

        context.user_data["last_image_answer"] = answer

        await send_long_message(
            update,
            answer
        )

    except Exception as e:

        traceback.print_exc()

        await update.message.reply_text(
            f"❌ حدث خطأ أثناء تحليل الصورة:\n{e}"
        )


# ============================================================
# VOICE / AUDIO
# ============================================================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        await update.message.reply_text(
            "🎤 جاري تحويل التسجيل إلى نص...\n"
            "قد يستغرق ذلك بعض الوقت."
        )

        voice = update.message.voice

        file = await voice.get_file()

        voice_dir = DATA_DIR / "voice"
        voice_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        input_file = (
            voice_dir
            / f"{user_id}_{voice.file_unique_id}.ogg"
        )

        await file.download_to_drive(
            custom_path=str(input_file),
            read_timeout=300,
            write_timeout=300,
            connect_timeout=60,
            pool_timeout=300,
        )

        transcript = await transcribe_audio_file(
            input_file
        )

        if not transcript:
            await update.message.reply_text(
                "❌ لم أستطع استخراج الكلام من التسجيل."
            )
            return

        await update.message.reply_text(
            "📝 تم تفريغ التسجيل.\n"
            "🧠 جاري تحليل المحتوى..."
        )

        prompt = (
            "لديك تفريغ صوتي لمحاضرة أو سؤال.\n\n"
            "حلل المحتوى التالي.\n"
            "إذا كان سؤالاً رياضياً فحله خطوة بخطوة.\n"
            "إذا كان جزءاً من محاضرة، لخصه واشرح "
            "النقاط المهمة والقوانين والأمثلة.\n\n"
            f"التفريغ:\n{transcript}"
        )

        # ========================================================
        # MATH ENGINE / GEMINI
        # ========================================================

        # ملاحظة:
        # هنا نستخدم transcript وليس text لأن handle_voice
        # لا يملك متغير text.

        math_result = None

        try:
            math_result = await asyncio.to_thread(
                solve_math,
                transcript
            )
        except Exception as math_error:
            print("⚠️ Math engine:", repr(math_error))

        if math_result:
            try:
                result_text = format_result(math_result)

                answer = (
                    "🧮 الحل الرياضي:\n\n"
                    f"{result_text}\n\n"
                    "✅ تم تحليل المسألة باستخدام محرك الرياضيات."
                )

                print(
                    "🧮 MATH ENGINE RESULT:",
                    result_text
                )

            except Exception as format_error:
                print(
                    "⚠️ Math result formatting error:",
                    repr(format_error)
                )

                answer = await asyncio.to_thread(
                    ask_gemini,
                    prompt,
                    conversation_memory.get(user_id),
                    persistent_memory.get_all(user_id)
                )

        else:
            # ====================================================
            # GEMINI FOR NORMAL / EXPLANATORY QUESTIONS
            # ====================================================

            answer = await asyncio.to_thread(
                ask_gemini,
                prompt,
                conversation_memory.get(user_id),
                persistent_memory.get_all(user_id)
            )

        if not answer:
            answer = "❌ لم يتم الحصول على إجابة."

        conversation_memory.add(
            user_id,
            "assistant",
            answer,
        )

        await send_long_message(
            update,
            answer
        )

    except Exception as e:
        print("\n========== ERROR ==========")

        traceback.print_exc()

        try:
            await update.message.reply_text(
                f"❌ حدث خطأ:\n"
                f"{type(e).__name__}\n"
                f"{e}"
            )
        except Exception:
            pass



async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    try:
        text = (update.message.text or "").strip()
        user_id = update.effective_user.id

        if not text:
            return

        # ====================================================
        # COMMAND / SPECIAL ROUTING
        # ====================================================

        # /pronounce يتم التعامل معه بواسطة Command/Message handler مستقل
        if text.startswith("/pronounce"):
            return

        # ====================================================
        # VIDEO GENERATION
        # ====================================================

        if is_video_generation_request(text):
            await handle_video_generation(
                update,
                context
            )
            return

        # ====================================================
        # ARABIC PRONUNCIATION
        # ====================================================

        # "انطق ..." يجب أن يذهب مباشرة إلى TTS
        # قبل الذاكرة و RAG و AgentV2.
        if text.startswith("انطق"):
            word = text[len("انطق"):].strip()

            if word:
                print("🔊 ARABIC TTS REQUEST:", word)

                await update.message.reply_text(
                    "🔊 جاري تجهيز النطق..."
                )

                audio_dir = DATA_DIR / "audio"
                audio_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                audio_path = (
                    audio_dir
                    / f"{update.effective_user.id}_pronunciation.mp3"
                )

                try:
                    await text_to_speech(
                        word,
                        str(audio_path)
                    )

                    print(
                        "🔊 TTS FILE:",
                        audio_path,
                        "exists=",
                        audio_path.exists()
                    )

                    with open(audio_path, "rb") as audio:
                        await update.message.reply_audio(
                            audio=audio,
                            title=f"Pronunciation: {word}"
                        )

                    print("✅ ARABIC TTS SENT")

                except Exception as e:
                    traceback.print_exc()

                    await update.message.reply_text(
                        f"❌ حدث خطأ أثناء إنشاء النطق:\n{e}"
                    )

                return

            await update.message.reply_text(
                "🔊 اكتب الكلمة بعد «انطق»."
            )
            return

        # ====================================================
        # NAME / MEMORY
        # ====================================================

        if "ما اسمي" in text or "شو اسمي" in text:
            saved_name = persistent_memory.get(
                user_id,
                "name"
            )

            if saved_name:
                await update.message.reply_text(
                    f"اسمك هو {saved_name}."
                )
                return

        if "اسمي" in text:
            name = text.replace(
                "اسمي",
                ""
            ).strip()

            if name:
                persistent_memory.remember(
                    user_id,
                    "name",
                    name
                )

        conversation_memory.add(
            user_id,
            "user",
            text
        )

        # ====================================================
        # IMAGE FOLLOW-UP HAS HIGH PRIORITY
        # ====================================================
        # إذا أرسل المستخدم صورة ثم قال:
        # "حل الباقي" / "كمل" / "حل 3 و4"
        # يجب إعادة استخدام نفس الصورة.
        # هذا يجب أن يحدث قبل RAG وMath Engine.
        # ====================================================

        last_image_path = context.user_data.get(
            "last_image_path"
        )

        image_followup_words = (
            "حل الباقي",
            "حل باقي",
            "كمل",
            "كمل الحل",
            "كمل باقي",
            "حل الأسئلة الباقية",
            "حل الاسئلة الباقية",
            "حل الباقي من الأسئلة",
            "حل الباقي من الاسئلة",
            "حل 2",
            "حل 3",
            "حل 4",
            "حل 5",
            "السؤال 2",
            "السؤال 3",
            "السؤال 4",
            "السؤال 5",
            "سؤال 1",
            "سؤال 2",
            "سؤال 3",
            "سؤال 4",
            "سؤال 5",
            "سؤال 6",
            "سؤال 7",
            "سؤال 8",
            "سؤال 9",
            "سؤال 10",
            "سؤال 11",
            "سؤال 12",
            "سؤال 13",
            "سؤال 14",
            "سؤال 15",
            "سؤال 16",
            "سؤال 17",
            "سؤال 18",
            "سؤال 19",
            "سؤال 20",
            "سؤال 21",
            "سؤال 2",
            "سؤال 3",
            "سؤال 4",
            "سؤال 5",
            "سؤال 6",
            "سؤال 7",
            "سؤال 8",
            "سؤال 9",
            "سؤال 10",
            "سؤال 11",
            "سؤال 12",
            "سؤال 13",
            "سؤال 14",
            "سؤال 15",
            "سؤال 16",
            "سؤال 17",
            "سؤال 18",
            "سؤال 19",
            "سؤال 20",
            "سؤال 21",
            "كيف اجت",
            "كيف جاءت",
            "كيف جبت",
            "من وين اجت",
            "من أين جاءت",
            "ليش",
            "لماذا",
            "اشرح",
            "وضح",
            "وضحلي",
        )

        is_image_followup = (
            bool(last_image_path)
            and Path(last_image_path).exists()
            and any(
                phrase in text.lower()
                for phrase in image_followup_words
            )
        )

        if is_image_followup:

            print(
                "🖼️ IMAGE FOLLOW-UP MODE:",
                text
            )

            await update.message.reply_text(
                "🖼️ سأستخدم نفس الصورة السابقة وأكمل "
                "جميع الأسئلة المتبقية..."
            )

            previous_answer = context.user_data.get(
                "last_image_answer",
                ""
            )

            followup_prompt = (
                "هذه متابعة لصورة أرسلها المستخدم سابقًا.\n\n"
                "استخدم الصورة كاملة مرة أخرى.\n\n"
                "الإجابة السابقة على الصورة كانت:\n"
                f"{previous_answer}\n\n"
                "المستخدم يطلب الآن:\n"
                f"{text}\n\n"
                "قواعد إلزامية:\n"
                "1. راجع الصورة كاملة.\n"
                "2. حدد جميع أرقام الأسئلة الموجودة فيها.\n"
                "3. قارنها مع الإجابة السابقة الموجودة في سياق المحادثة "
                "إن كانت متاحة.\n"
                "4. حل الأسئلة التي طلبها المستخدم أو الأسئلة المتبقية.\n"
                "5. لا تكتف بسؤال واحد إذا كان هناك أكثر من سؤال مطلوب.\n"
                "6. لكل سؤال اذكر القانون المستخدم.\n"
                "7. لا تخترع أي سؤال أو رقم غير واضح.\n"
                "8. إذا كانت كل الأسئلة واضحة، أكمل حتى آخر سؤال مطلوب.\n\n"
                "أعطِ الحل الكامل والمنظم."
            )

            answer = await asyncio.to_thread(
                analyze_image,
                str(last_image_path),
                followup_prompt
            )

            conversation_memory.add(
                user_id,
                "user",
                text
            )

            conversation_memory.add(
                user_id,
                "assistant",
                answer
            )

            await send_long_message(
                update,
                answer
            )

            return

        # ====================================================
        # AI IMAGE GENERATION
        # ====================================================

        image_request = any(
            phrase in text.lower()
            for phrase in (
                "اعمل صورة",
                "اعمللي صورة",
                "اعمل لي صورة",
                "سوي صورة",
                "سويلي صورة",
                "سوي لي صورة",
                "أنشئ صورة",
                "انشئ صورة",
                "ولد صورة",
                "ولّد صورة",
                "اصنع صورة",
                "صمم صورة",
                "ارسم صورة",
                "generate image",
                "create image",
                "make an image",
            )
        )

        if image_request:
            await update.message.reply_text(
                "🎨 جاري توليد الصورة..."
            )

            try:
                image_dir = DATA_DIR / "generated_images"

                image_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                filename = (
                    f"{update.effective_user.id}_"
                    f"{uuid.uuid4().hex}.png"
                )

                image_path = await asyncio.to_thread(
                    generate_image,
                    text,
                    filename
                )

                with open(image_path, "rb") as image:
                    await update.message.reply_photo(
                        photo=image,
                        caption="🎨 تم توليد الصورة."
                    )

                return

            except Exception as e:
                print(
                    "IMAGE GENERATION ERROR:",
                    repr(e)
                )

                await update.message.reply_text(
                    "❌ تعذر توليد الصورة حاليًا.\n\n"
                    f"{e}"
                )

                return

        # ====================================================
        # MATH HAS HIGH PRIORITY
        # ====================================================

        math_words = (
            "احسب",
            "حل",
            "أوجد",
            "اوجد",
            "مشتقة",
            "مشتق",
            "تكامل",
            "اشتق",
            "معادلة",
            "برهن",
            "اثبت",
            "أثبت",
            "نهاية",
            "لوغاريتم",
            "جذر",
            "مصفوفة",
            "متجه",
            "تفاضل",
            "رياضيات",
        )

        lower_text = text.lower()

        is_math_request = any(
            word in lower_text
            for word in math_words
        )

        # طلب مثال من درس محدد يجب أن يذهب إلى
        # Document Intelligence وليس Math Engine.
        is_document_example_request = bool(
            re.search(
                r"(?:المثال|مثال)\s*\d+\s*(?:من\s*)?(?:الدرس|درس)\s*\d+(?:\.\d+)?",
                lower_text,
                flags=re.IGNORECASE,
            )
            or re.search(
                r"(?:الدرس|درس)\s*\d+(?:\.\d+)?\s*(?:المثال|مثال)\s*\d+",
                lower_text,
                flags=re.IGNORECASE,
            )
            or re.search(
                r"(?:example)\s*\d+\s*(?:from\s*)?(?:lesson)\s*\d+(?:\.\d+)?",
                lower_text,
                flags=re.IGNORECASE,
            )
        )

        if is_document_example_request:
            is_math_request = False

        # ====================================================
        # DIRECT MATH ENGINE
        # ====================================================
        # إذا كان هناك ملف/RAG نشط، لا تستخدم Math Engine
        # لأن السؤال قد يكون عن أسئلة موجودة داخل الملف.
        # يجب أن يمر السؤال إلى FILE-ONLY RAG.
        # ====================================================

        active_file_rag = (
            "rag" in context.user_data
            or "current_file" in context.user_data
        )

        if is_math_request and not active_file_rag:
            try:
                result = await asyncio.to_thread(
                    solve_math,
                    text
                )

                if result is not None:
                    formatted = format_result(result)

                    conversation_memory.add(
                        user_id,
                        "assistant",
                        formatted
                    )

                    await send_long_message(
                        update,
                        "🧮 " + formatted
                    )

                    return

                print(
                    "DIRECT MATH ENGINE RETURNED NONE:",
                    text
                )

            except Exception as math_error:
                print(
                    "DIRECT MATH ERROR:",
                    repr(math_error)
                )

        # ====================================================
        # WAITING MESSAGE
        # ====================================================

        waiting = get_waiting_message(text)

        if waiting:
            await update.message.reply_text(
                waiting
            )

        # ====================================================
        # RESTORE PERSISTENT RAG
        # ====================================================

        file_context = ""

        if "rag" not in context.user_data:
            saved_document = persistent_rag.get_document(
                user_id
            )

            if saved_document:
                print(
                    "♻️ Restoring persistent document..."
                )

                rag = RAGManager()

                rag.load_document(
                    user_id,
                    saved_document["content"],
                    filename=saved_document.get("file_info", {}).get("filename"),
                )

                context.user_data["rag"] = rag

                context.user_data["current_file"] = (
                    saved_document.get(
                        "file_info",
                        {}
                    )
                )

                print(
                    "✅ Persistent document restored"
                )

        # ====================================================
        # STRICT FILE / RAG MODE
        # ====================================================

        file_context = ""
        file_mode = False

        # ----------------------------------------------------
        # استعادة الملف المحفوظ
        # ----------------------------------------------------

        if "rag" not in context.user_data:

            saved_document = persistent_rag.get_document(
                user_id
            )

            if saved_document:

                print(
                    "♻️ Restoring persistent document..."
                )

                rag = RAGManager()

                rag.load_document(
                    user_id,
                    saved_document["content"],
                    filename=saved_document.get("file_info", {}).get("filename"),
                )

                context.user_data["rag"] = rag

                context.user_data["current_file"] = (
                    saved_document.get(
                        "file_info",
                        {}
                    )
                )

                print(
                    "✅ Persistent document restored"
                )


        # ----------------------------------------------------
        # إذا يوجد ملف للمستخدم:
        # ندخل وضع FILE-ONLY
        # ----------------------------------------------------

        if "rag" in context.user_data:

            # الملف المحفوظ لا يعني أن كل رسالة يجب أن تكون FILE-ONLY.
            # فعّل RAG فقط عندما تكون الرسالة مرتبطة بوضوح بالملف/الكتاب.
            file_query_words = (
                "في الملف",
                "بالملف",
                "من الملف",
                "داخل الملف",
                "عن الملف",
                "من الكتاب",
                "في الكتاب",
                "بالكتاب",
                "داخل الكتاب",
                "عن الكتاب",
                "الكتاب",
                "الملف",
                "الصفحة",
                "الصفحات",
                "الفصل",
                "الدرس",
                "المثال",
                "الأمثلة",
                "القانون الموجود",
                "حسب الملف",
                "حسب الكتاب",
                "الفهرس",
                "فهرس",
                "جدول المحتويات",
                "المحتويات",
                "محتويات الكتاب",
                "من الصورة",
                  # ------------------------------------------------
                  # أسئلة طبيعية عن الملف/الكتاب
                  # ------------------------------------------------
                  "خلفية عن الملف",
                  "خلفية عن الكتاب",
                  "خلفية للملف",
                  "خلفية للكتاب",
                  "فكرة عن الملف",
                  "فكرة عن الكتاب",
                  "فكرة عامة عن الملف",
                  "فكرة عامة عن الكتاب",
                  "فكرة عامة",
                  "نبذة عن الملف",
                  "نبذة عن الكتاب",
                  "نبذة",
                  "احكيلي عن الملف",
                  "احكي لي عن الملف",
                  "احكيلي عن الكتاب",
                  "احكي لي عن الكتاب",
                  "احكي عن الملف",
                  "احكي عن الكتاب",
                  "شو موضوع الملف",
                  "شو موضوع الكتاب",
                  "شو محتوى الملف",
                  "شو محتوى الكتاب",
                  "شو أهم مواضيع الملف",
                  "شو أهم مواضيع الكتاب",
                  "أهم مواضيع الملف",
                  "أهم مواضيع الكتاب",
                  "شو بتعلم من الكتاب",
                  "شو رح أتعلم من الكتاب",
                  "ماذا سأتعلم من الكتاب",
                "في الصورة",
            )

            image_context_words = (
                "الصورة السابقة",
                "الصورة",
                "حل الباقي",
                "كمل الحل",
                "كمل",
            )

            text_lower = text.lower()

            is_file_query = any(
                word in text_lower
                for word in file_query_words
            )

            is_image_context = any(
                word in text_lower
                for word in image_context_words
            )

            file_mode = (
                is_file_query
                and not is_image_context
            )

            if not file_mode:
                print(
                    "📚 FILE EXISTS BUT GENERAL MODE:",
                    text
                )
            else:
                rag = context.user_data["rag"]

                # تهيئة المتغير قبل أي مسار لاحق
                relevant_chunks = []

                print(
                    "📚 FILE-ONLY MODE ENABLED"
                )

                print(
                    "📚 FILE-ONLY MODE ENABLED"
                )

                # ====================================================
                # DOCUMENT INTELLIGENCE — PRIORITY
                # ====================================================
                # افحص الفهرس البنيوي أولاً قبل RAG التقليدي.
                # هذا مهم لطلبات مثل:
                # "اشرحلي درس 2"
                # "محتوى الدرس 3"
                # "أعطني معلومات عن الاشتقاق"
                # ====================================================

                try:
                    # ====================================================
                    # ====================================================
                    # DIRECT TOC — PRIORITY
                    # ====================================================
                    # الفهرس لا يذهب إلى Gemini.
                    # نأخذه مباشرة من RAG، ثم DocumentIndex كـ fallback.
                    # ====================================================

                    toc_triggers = (
                        "فهرس",
                        "الفهرس",
                        "فهرس الكتاب",
                        "هات الفهرس",
                        "هاتلي الفهرس",
                        "هاتلي فهرس",
                        "اعطني الفهرس",
                        "أعطني الفهرس",
                        "اعطني فهرس",
                        "أعطني فهرس",
                        "جدول المحتويات",
                        "محتويات الكتاب",
                        "محتويات",
                        "table of contents",
                        "toc",
                    )

                    query_lower = text.strip().lower()

                    if any(trigger in query_lower for trigger in toc_triggers):
                        print("📚 DIRECT TOC REQUEST DETECTED")

                        # ------------------------------------------------
                        # 1) RAG TOC — المصدر المباشر
                        # ------------------------------------------------
                        try:
                            toc = rag.table_of_contents(user_id=user_id)

                            if toc and str(toc).strip():
                                answer = (
                                    "📚 فهرس الكتاب:\n\n"
                                    + str(toc).strip()
                                )

                                print("📚 DIRECT RAG TOC ANSWERED")

                                conversation_memory.add(
                                    user_id,
                                    "assistant",
                                    answer,
                                )

                                await send_long_message(
                                    update,
                                    answer,
                                )

                                return

                            print("⚠️ RAG TOC EMPTY")

                        except Exception as toc_error:
                            print(
                                "⚠️ DIRECT RAG TOC ERROR:",
                                repr(toc_error),
                            )

                        # ------------------------------------------------
                        # 2) DocumentIndex — fallback
                        # ------------------------------------------------
                        try:
                            document = rag.get_document(user_id)

                            if document:
                                from core.document_intelligence.document import parse_document
                                from core.document_intelligence.structure import DocumentStructureAnalyzer
                                from core.document_intelligence.index import DocumentIndex

                                parsed_document = parse_document(
                                    document.get("content", ""),
                                    filename=document.get(
                                        "file_info", {}
                                    ).get(
                                        "filename",
                                        "document.pdf",
                                    ),
                                )

                                structure = DocumentStructureAnalyzer().analyze(
                                    parsed_document
                                )

                                document_index = DocumentIndex(
                                    parsed_document,
                                    structure,
                                )

                                toc = document_index.table_of_contents()

                                if toc and str(toc).strip():
                                    answer = (
                                        "📚 فهرس الكتاب:\n\n"
                                        + str(toc).strip()
                                    )

                                    print(
                                        "📚 DOCUMENT INDEX TOC ANSWERED"
                                    )

                                    conversation_memory.add(
                                        user_id,
                                        "assistant",
                                        answer,
                                    )

                                    await send_long_message(
                                        update,
                                        answer,
                                    )

                                    return

                            print("⚠️ DOCUMENT INDEX TOC EMPTY")

                        except Exception as toc_error:
                            print(
                                "⚠️ DOCUMENT INDEX TOC ERROR:",
                                repr(toc_error),
                            )

                    # لا يوجد تطابق في الفهرس،
                        # ننتقل إلى RAG التقليدي.
                        relevant_chunks = rag.search(
                            user_id,
                            text
                        )

                        print(
                            "RAG CHUNKS:",
                            len(relevant_chunks)
                        )

                except Exception as di_error:
                    print(
                        "⚠️ DOCUMENT INTELLIGENCE QUERY ERROR:",
                        repr(di_error),
                    )

                    # في حال فشل DI لا نعطل النظام القديم.
                    relevant_chunks = rag.search(
                        user_id,
                        text
                    )

                    print(
                        "RAG CHUNKS:",
                        len(relevant_chunks)
                    )


                # ------------------------------------------------
                # BOOK-WIDE REQUEST
                # ------------------------------------------------
                # الطلبات التي تتعلق بالكتاب كله لا تعتمد على نتائج
                # البحث بالكلمات. نأخذ المحتوى الكامل مباشرة من RAG.
                # ------------------------------------------------

                if rag.searcher.is_book_wide_query(text):

                    relevant_chunks = rag.index.get_all(user_id)

                    print(
                        "📚 BOOK-WIDE: loaded all RAG chunks:",
                        len(relevant_chunks),
                    )

                    if not relevant_chunks:
                        answer = (
                            "❌ لا يوجد محتوى كافٍ في الملف "
                            "لتحليل هذا الطلب."
                        )

                        conversation_memory.add(
                            user_id,
                            "assistant",
                            answer,
                        )

                        await send_long_message(
                            update,
                            answer,
                        )

                        return

                    await update.message.reply_text(
                        "📚 وجدت طلبًا يغطي الكتاب/نطاقًا كبيرًا.\n"
                        "🧠 سأحلله على دفعات من محتوى الملف فقط..."
                    )

                    answer = await summarize_book(
                        relevant_chunks,
                        text,
                    )

                    if not answer:
                        answer = (
                            "❌ لم أتمكن من استخراج إجابة "
                            "من الملف لهذا الطلب."
                        )

                    conversation_memory.add(
                        user_id,
                        "assistant",
                        answer,
                    )

                    await send_long_message(
                        update,
                        answer,
                    )

                    return


                # ------------------------------------------------
                # سؤال محدد
                # ------------------------------------------------

                if relevant_chunks:

                    file_context = "\n\n".join(
                        relevant_chunks
                    )

                    print(
                        "📖 FILE CONTEXT FOUND:",
                        len(file_context)
                    )

                else:

                    # ------------------------------------------------
                    # حماية مهمة:
                    # لا Gemini
                    # لا AgentV2
                    # لا Web
                    # لا KnowledgeBase
                    # ------------------------------------------------

                    answer = (
                        "❌ لم أجد إجابة هذا السؤال داخل الملف.\n\n"
                        "أنا الآن أجيب اعتمادًا على الملف المرفق فقط، "
                        "ولن أستخدم معلومات من خارجه."
                    )

                    print(
                        "🚫 FILE-ONLY: No relevant chunks found."
                    )

                    conversation_memory.add(
                        user_id,
                        "assistant",
                        answer
                    )

                    await send_long_message(
                        update,
                        answer
                    )

                    return


        # ====================================================
        # ====================================================
        # ====================================================
        # DOCUMENT INTELLIGENCE QUERY
        # ====================================================
        #
        # الفهرس البنيوي له الأولوية على البحث التقليدي.
        # إذا وجد درسًا مطابقًا، نستخدم محتواه من الملف.
        # إذا لم يجد، نستمر إلى المسار الحالي.
        #

        if file_mode:
            try:
                rag = context.user_data["rag"]

                di_mode, di_result = _document_intelligence_query(
                    rag,
                    user_id,
                    text,
                )

                if di_mode == "answer":
                    answer = di_result

                    print(
                        "📚 DOCUMENT INTELLIGENCE DIRECT ANSWER"
                    )

                    conversation_memory.add(
                        user_id,
                        "assistant",
                        answer,
                    )

                    await send_long_message(
                        update,
                        answer,
                    )

                    return

                elif di_mode == "context":
                    file_context = di_result

                    print(
                        "📚 DOCUMENT INTELLIGENCE CONTEXT FOUND:",
                        len(file_context),
                    )

                    relevant_chunks = [file_context]

            except Exception as di_error:
                print(
                    "⚠️ DOCUMENT INTELLIGENCE QUERY ERROR:",
                    repr(di_error),
                )

        # AGENT V2
        # ====================================================

        # AgentV2 يعمل فقط عندما لا يوجد ملف نشط.
        if not file_mode:

            try:

                global agent_v2

                if "agent_v2" not in globals():

                    agent_v2 = AgentV2()

                agent_result = await asyncio.to_thread(
                    agent_v2.chat,
                    text,
                    user_id
                )

                if isinstance(agent_result, dict):

                    answer = (
                        agent_result.get("response")
                        or agent_result.get("output")
                        or str(agent_result)
                    )

                else:

                    answer = str(
                        agent_result
                    )

                print(
                    "🤖 AgentV2 RESPONSE:",
                    answer[:500]
                )


            except Exception as agent_error:

                print(
                    "❌ AgentV2 ERROR:",
                    repr(agent_error)
                )

                # SAFE GEMINI FALLBACK

                answer = await asyncio.to_thread(
                    ask_gemini,
                    text,
                    conversation_memory.get(user_id),
                    persistent_memory.get_all(user_id)
                )


        # ====================================================
        # FILE / RAG ANSWER
        # ====================================================

        else:

            # ------------------------------------------------
            # Gemini مسموح له هنا فقط بتحليل النص المستخرج
            # من الملف.
            # ------------------------------------------------

            # ------------------------------------------------
            # SPECIAL EXAMPLE SOLVER
            # ------------------------------------------------
            # إذا كان المحتوى مثالًا محددًا، نطلب من النموذج
            # إعادة بناء المسألة من OCR وحلها خطوة بخطوة،
            # بدل التعامل معها كسياق كتاب عام.
            is_example_request = (
                "المثال" in text
                or "مثال" in text
                or "example" in text.lower()
            )

            if is_example_request:
                prompt = (
                    "أنت أستاذ رياضيات تشرح المثال الموجود في الكتاب.\n\n"
                    "المحتوى التالي مستخرج من PDF بواسطة OCR، "
                    "وقد يحتوي على مسافات أو رموز رياضية مشوهة.\n"
                    "مهمتك أن تفهم المعادلة رياضيًا من السياق، "
                    "ثم تحل المثال خطوة بخطوة.\n\n"
                    "ممنوع نسخ رموز OCR المشوهة كما هي.\n"
                    "ممنوع اختراع أرقام غير موجودة في المثال.\n"
                    "حافظ على المتغيرات والعمليات الرياضية الصحيحة.\n"
                    "اكتب التكاملات والكسور والأسس بصيغة واضحة.\n"
                    "اذكر التعويض u إن كان المثال يستخدم طريقة التعويض.\n"
                    "وفي النهاية اكتب الإجابة النهائية بوضوح.\n\n"
                    "EXAMPLE FROM BOOK:\n"
                    + file_context
                    + "\n\n"
                    "USER QUESTION:\n"
                    + text
                    + "\n\n"
                    "أجب بالعربية وبشرح تعليمي خطوة بخطوة."
                )

            else:
                prompt = (
                    "أنت مساعد دراسي يعمل في وضع الملف فقط.\n\n"

                    "قاعدة صارمة جدًا:\n"
                "اعتمد فقط على محتوى الملف الموجود في "
                "FILE CONTENT.\n"

                "ممنوع استخدام معلومات خارج الملف.\n"
                "ممنوع البحث في الإنترنت.\n"
                "ممنوع الاعتماد على المعرفة العامة.\n"
                "إذا لم توجد الإجابة في المحتوى المقدم، "
                "قل بوضوح إن المعلومات غير موجودة في الملف.\n\n"

                "FILE CONTENT:\n"
                + file_context
                + "\n\n"

                "USER QUESTION:\n"
                + text
                + "\n\n"

                "أجب بالعربية وبشرح واضح، "
                "وإذا كانت المسألة رياضية فحلها اعتمادًا "
                "على المعطيات والقواعد الموجودة في الملف."
            )

            answer = await asyncio.to_thread(
                ask_gemini,
                prompt,
                conversation_memory.get(user_id),
                persistent_memory.get_all(user_id),
            )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        if not answer:
            answer = "❌ لم يتم الحصول على إجابة."

        conversation_memory.add(
            user_id,
            "assistant",
            answer
        )

        context.user_data["last_image_answer"] = answer

        await send_long_message(
            update,
            answer
        )

    except Exception as e:
        print("\n========== ERROR ==========")

        traceback.print_exc()

        try:
            await update.message.reply_text(
                f"❌ حدث خطأ:\n"
                f"{type(e).__name__}\n"
                f"{e}"
            )
        except Exception:
            pass




# ============================================================
# DOCUMENT INTELLIGENCE QUERY HELPER
# ============================================================

def _document_intelligence_query(rag, user_id, query):
    """
    يستخدم الفهرس البنيوي للوثيقة قبل RAG التقليدي.

    يدعم أرقام الدروس العشرية مثل:
    1.1
    2.2
    5.5
    6.4
    """

    import re

    query = (query or "").strip()

    if not query:
        return None, None

    lower = query.lower()

    # --------------------------------------------------------
    # 0) طلب مثال محدد من درس محدد
    # --------------------------------------------------------

    example_patterns = (
        r"(?:المثال|مثال)\s*(\d+)\s*(?:من\s*)?(?:الدرس|درس)\s*(\d+(?:\.\d+)?)",
        r"(?:الدرس|درس)\s*(\d+(?:\.\d+)?)\s*(?:المثال|مثال)\s*(\d+)",
        r"(?:example)\s*(\d+)\s*(?:from\s*)?(?:lesson)\s*(\d+(?:\.\d+)?)",
    )

    for pattern_index, pattern in enumerate(example_patterns):

        match = re.search(
            pattern,
            lower,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        if pattern_index == 1:
            lesson_number = match.group(1)
            example_number = int(match.group(2))
        else:
            example_number = int(match.group(1))
            lesson_number = match.group(2)

        example = rag.get_example(
            user_id=user_id,
            lesson_number=lesson_number,
            example_number=example_number,
        )

        if example:

            return (
                "context",
                (
                    f"📚 الدرس {example.lesson_number}\n"
                    f"📝 المثال {example.number}\n"
                    f"📄 الصفحة {example.page_number}\n\n"
                    f"{example.text}"
                ),
            )

    # --------------------------------------------------------
    # 1) طلب درس برقم
    # --------------------------------------------------------

    lesson_patterns = (
        r"(?:الدرس|درس)\s*(\d+(?:\.\d+)?)",
        r"(?:lesson)\s*(\d+(?:\.\d+)?)",
    )

    for pattern in lesson_patterns:

        match = re.search(
            pattern,
            lower,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        number_text = match.group(1)

        try:
            number = float(number_text)
        except ValueError:
            continue

        lesson = rag.get_lesson(
            user_id=user_id,
            number=number,
        )

        if lesson:

            lesson_text = rag.get_lesson_text(
                user_id=user_id,
                lesson=lesson,
            )

            if lesson_text:

                return (
                    "context",
                    (
                        f"📚 الدرس {lesson.number}: {lesson.title}\n"
                        f"📖 الوحدة: {lesson.unit_title or 'غير محددة'}\n"
                        f"📄 الصفحات: "
                        f"{lesson.start_page}-{lesson.end_page}\n\n"
                        f"{lesson_text}"
                    ),
                )

    # --------------------------------------------------------
    # 2) البحث باسم الدرس
    # --------------------------------------------------------

    search_triggers = (
        "اشرح",
        "شرح",
        "محتوى",
        "ما هو",
        "ما هي",
        "أين يوجد",
        "أين أجد",
        "اعطني",
        "أعطني",
        "معلومات عن",
        "تكلم عن",
        "تكلم حول",
        "فهرس",
        "الفهرس",
        "جدول المحتويات",
        "محتويات الكتاب",
        "محتويات",
        "toc",
        "table of contents",
    )

    if any(trigger in lower for trigger in search_triggers):

        results = rag.search_lessons(
            user_id=user_id,
            query=query,
        )

        if results:

            lesson = results[0]

            lesson_text = rag.get_lesson_text(
                user_id=user_id,
                lesson=lesson,
            )

            if lesson_text:

                return (
                    "context",
                    (
                        f"📚 الدرس {lesson.number}: {lesson.title}\n"
                        f"📖 الوحدة: {lesson.unit_title or 'غير محددة'}\n"
                        f"📄 الصفحات: "
                        f"{lesson.start_page}-{lesson.end_page}\n\n"
                        f"{lesson_text}"
                    ),
                )

    return None, None

def parse_page_range(text):
    import re

    text = (text or "").strip()

    patterns = [
        r"(?:من\s*)?(?:الصفحات?|صفحة|pages?|page)\s*(\d+)\s*(?:إلى|الى|حتى|to|-|–|—)\s*(\d+)",
        r"(\d+)\s*(?:إلى|الى|حتى|to|-|–|—)\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            return int(match.group(1)), int(match.group(2))

    return None

def extract_requested_duration(text: str, default=20):
    """
    يحاول استخراج مدة الفيديو من طلب المستخدم.

    أمثلة:
    20 ثانية
    مدته 30 ثانية
    لمدة 15 ثانية
    1 دقيقة
    """

    import re

    text_lower = text.lower()

    # ثواني
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:ثانية|ثواني|second|seconds|sec|s)",
        text_lower
    )

    if match:
        return float(match.group(1))

    # دقائق
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:دقيقة|دقائق|minute|minutes|min)",
        text_lower
    )

    if match:
        return float(match.group(1)) * 60

    return float(default)

def extract_pdf_pages(pdf_path, start_page, end_page, user_id):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    start_page = int(start_page)
    end_page = int(end_page)

    if start_page < 1 or end_page < 1:
        raise ValueError("رقم الصفحة يجب أن يكون أكبر من صفر.")

    if start_page > end_page:
        raise ValueError("صفحة البداية يجب أن تكون قبل صفحة النهاية.")

    if end_page > total_pages:
        raise ValueError(
            f"الملف يحتوي على {total_pages} صفحة فقط."
        )

    output_dir = DATA_DIR / "extracted_pages"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir
        / f"{user_id}_pages_{start_page}_{end_page}.pdf"
    )

    writer = PdfWriter()

    for index in range(start_page - 1, end_page):
        writer.add_page(reader.pages[index])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path, total_pages

def get_waiting_message(text: str):
    text = text.strip().lower()

    greetings = [
        "مرحبا",
        "السلام عليكم",
        "هلا",
        "اهلا",
        "أهلا",
        "صباح الخير",
        "مساء الخير",
        "كيف حالك",
        "شلونك",
    ]

    math_keywords = [
        "احسب",
        "حل",
        "معادلة",
        "تكامل",
        "تفاضل",
        "مشتقة",
        "رياضيات",
        "برهن",
        "اثبت",
        "أثبت",
        "نهاية",
        "لوغاريتم",
        "جذر",
        "مصفوفة",
        "متجه",
    ]

    if any(word in text for word in greetings):
        return None

    if any(word in text for word in math_keywords):
        return "🧠 جاري تحليل المسألة..."

    if len(text) > 150:
        return "📚 جاري إعداد الإجابة..."

    return "🤔 جاري التفكير..."

def enhance_educational_video_request(text: str) -> str:
    """
    يحوّل طلبات شرح الرياضيات بأسلوب الورقة والقلم
    إلى تعليمات واضحة لمولّد الفيديو.
    """
    q = text.strip().lower()

    educational_terms = (
        "ورقة", "قلم", "الورقة والقلم",
        "شرح", "اشرح", "تعليمي",
        "رياضيات", "دالة", "الدوال",
        "اختبار الخط الرأسي", "الخط الرأسي",
        "vertical line test",
        "function"
    )

    if not any(term in q for term in educational_terms):
        return text

    return f"""
أنشئ فيديو تعليمي رياضي بأسلوب شرح حقيقي على ورقة بيضاء باستخدام قلم.

الموضوع المطلوب:
{text}

أسلوب الفيديو:
- تصوير علوي مباشر للورقة والقلم.
- يد تكتب على الورقة تدريجياً أمام المشاهد.
- لا تستخدم مشاهد سينمائية أو شخصيات أو أماكن غير ضرورية.
- التركيز الأساسي على الكتابة والرسم الرياضي.
- اكتب الرموز والمعادلات بوضوح وبشكل كبير.
- اجعل كل خطوة تظهر تدريجياً مع حركة القلم.
- استخدم رسومات بيانية بسيطة ودقيقة.
- عند شرح اختبار الخط الرأسي، ارسم محور x ومحور y ثم ارسم منحنى.
- ارسم خطاً رأسياً متحركاً على الرسم.
- وضّح حالة يقطع فيها الخط الرسم في نقطة واحدة: هذه دالة.
- وضّح حالة يقطع فيها الخط الرسم في نقطتين: ليست دالة.
- اكتب بجانب الرسم:
  "نقطة واحدة → دالة"
  "نقطتان أو أكثر → ليست دالة"
- اجعل الشرح مناسباً لطالب رياضيات في المدرسة.
- لا تخترع قوانين أو نتائج رياضية.
- الأولوية للدقة الرياضية والوضوح، وليس للمؤثرات البصرية.

يجب أن يبدو الفيديو كأن مدرس رياضيات يشرح للطالب بالورقة والقلم خطوة بخطوة.
"""

def build_cinematic_scene_files(plan):
    """
    ينشئ ملفات الفيديو لكل لقطة في VideoSequence.
    """

    scene_files = []

    for index, shot in enumerate(plan.shots, 1):

        print(
            f"🎬 Rendering shot {index}/"
            f"{len(plan.shots)} | "
            f"{shot.camera} | "
            f"{shot.duration}s"
        )

        scene_file = create_scene(
            scene_number=index,
            title=plan.title,
            description=shot.visual,
            duration=shot.duration,
            camera=shot.camera,
            effects=shot.effects,
            text=shot.text or "",
        )

        scene_files.append(scene_file)

    return scene_files

def combine_scenes(scene_files, output_path):
    """
    يجمع لقطات الفيديو بدون narration باستخدام FFmpeg.
    """
    if not scene_files:
        raise ValueError("لا توجد لقطات لتجميعها.")

    # إنشاء ملف نصي بقائمة الملفات
    list_file = Path(output_path).parent / "concat_list.txt"
    with open(list_file, "w") as f:
        for scene in scene_files:
            f.write(f"file '{scene}'\n")

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c",
        "copy",
        str(output_path),
    ]

    run_command(command)

    # تنظيف الملفات المؤقتة
    for scene in scene_files:
        try:
            Path(scene).unlink()
        except Exception:
            pass

    try:
        list_file.unlink()
    except Exception:
        pass

async def handle_video_generation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    المسار الكامل:

    User
       ↓
    build_video_plan
       ↓
    plan_text_to_sequence
       ↓
    create_scene × N
       ↓
    combine_scenes
       ↓
    Telegram
    """

    try:
        user_id = update.effective_user.id
        text = update.message.text.strip()

        # دعم فيديوهات الشرح التعليمي بأسلوب الورقة والقلم
        text = enhance_educational_video_request(text)

        requested_duration = extract_requested_duration(
            text,
            default=20
        )

        await update.message.reply_text(
            "🎬 تمام، فهمت طلب الفيديو.\n\n"
            f"⏱️ المدة المطلوبة: {requested_duration:g} ثانية\n"
            "🧠 جاري بناء الـ Shot Plan..."
        )

        # ----------------------------------------------------
        # BUILD PLAN
        # ----------------------------------------------------

        plan_text = await asyncio.to_thread(
            build_video_plan,
            text
        )

        if not plan_text:
            raise RuntimeError(
                "مولّد خطة الفيديو لم يُرجع خطة."
            )

        print("\n========== VIDEO PLAN ==========")
        print(plan_text)

        # ----------------------------------------------------
        # ADAPT PLAN
        # ----------------------------------------------------

        plan = plan_text_to_sequence(
            plan_text
        )

        if not plan.shots:
            raise RuntimeError(
                "لم يتم إنشاء أي لقطات."
            )

        # ----------------------------------------------------
        # FORCE REQUESTED DURATION
        # ----------------------------------------------------

        target_duration = requested_duration

        current_duration = plan.duration

        if current_duration <= 0:
            raise RuntimeError(
                "مدة اللقطات غير صالحة."
            )

        # نحافظ على عدد اللقطات ونوزع المدة
        # المطلوبة عليها بشكل نسبي.
        scale = (
            target_duration /
            current_duration
        )

        for shot in plan.shots:
            shot.duration = max(
                1.0,
                shot.duration * scale
            )

        # تصحيح آخر لقطة حتى تصبح المدة أقرب
        # ما يمكن للمدة المطلوبة.
        difference = (
            target_duration -
            plan.duration
        )

        if abs(difference) > 0.01:
            plan.shots[-1].duration = max(
                1.0,
                plan.shots[-1].duration + difference
            )

        print(
            "FINAL PLAN DURATION:",
            plan.duration
        )

        # ----------------------------------------------------
        # SHOW PLAN TO USER
        # ----------------------------------------------------

        await update.message.reply_text(
            "🎞️ تم بناء الخطة.\n"
            f"🎬 عدد اللقطات: {len(plan.shots)}\n"
            f"⏱️ المدة: {plan.duration:.1f} ثانية\n\n"
            "🔥 جاري تنفيذ اللقطات..."
        )

        # ----------------------------------------------------
        # RENDER SCENES
        # ----------------------------------------------------

        scene_files = await asyncio.to_thread(
            build_cinematic_scene_files,
            plan
        )

        if not scene_files:
            raise RuntimeError(
                "لم يتم إنشاء ملفات اللقطات."
            )

        # ----------------------------------------------------
        # COMBINE + ARABIC NARRATION
        # ----------------------------------------------------

        video_dir = (
            DATA_DIR /
            "videos" /
            "generated"
        )

        audio_dir = (
            DATA_DIR /
            "audio" /
            "video_narration"
        )

        video_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        audio_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output = (
            video_dir /
            f"cinematic_{user_id}_"
            f"{update.message.message_id}.mp4"
        )

        narration_path = (
            audio_dir /
            f"narration_{user_id}_"
            f"{update.message.message_id}.mp3"
        )

        # نص عربي تعليمي مناسب لطلب اختبار الخط الرأسي.
        # إذا كان الطلب عن موضوع آخر نستخدم نصاً عاماً من الطلب.
        if any(
            word in text
            for word in [
                "الخط الرأسي",
                "اختبار الخط",
                "vertical line",
                "vertical line test",
                "دالة أم لا",
                "هل الرسم دالة",
            ]
        ):
            narration_text = (
                "اليوم سنتعلم اختبار الخط الرأسي لمعرفة هل الرسم البياني يمثل دالة أم لا. "
                "أولاً نرسم أو ننظر إلى الرسم البياني. "
                "ثم نتخيل خطاً رأسياً يتحرك من اليسار إلى اليمين. "
                "إذا قطع الخط الرأسي الرسم في نقطة واحدة فقط في كل مكان، فالرسم يمثل دالة. "
                "أما إذا قطعه في نقطتين أو أكثر، فالرسم ليس دالة. "
                "مثلاً الدائرة ليست دالة، لأن بعض الخطوط الرأسية تقطعها في نقطتين. "
                "أما القطع المكافئ الذي يفتح إلى أعلى فهو دالة."
            )
        else:
            narration_text = (
                "مرحباً بكم في MathProfessor. "
                + text
            )

        await update.message.reply_text(
            "🎙️ جاري إنشاء الشرح الصوتي بالعربية..."
        )

        await text_to_speech(
            narration_text,
            str(narration_path)
        )

        if not narration_path.exists():
            raise RuntimeError(
                "فشل إنشاء ملف الشرح الصوتي."
            )

        print(
            "🎙️ NARRATION:",
            narration_path
        )

        await update.message.reply_text(
            "🎬 جاري دمج الفيديو مع الصوت..."
        )

        generated_output = await asyncio.to_thread(
            create_video_from_scenes,
            scene_files,
            str(narration_path)
        )

        # create_video_from_scenes يعيد المسار الحقيقي للفيديو النهائي.
        generated_output = Path(generated_output)

        if not generated_output.exists():
            raise RuntimeError(
                "تم إنشاء المشاهد والصوت لكن ملف الفيديو النهائي غير موجود."
            )

        # نسخ الفيديو النهائي إلى مجلد generated الخاص بالمستخدم.
        import shutil

        shutil.copy2(
            generated_output,
            output
        )

        if not output.exists():
            raise RuntimeError(
                "تم تنفيذ الفيديو لكن الملف النهائي غير موجود."
            )

        print(
            "🎥 FINAL VIDEO WITH ARABIC VOICE:",
            output
        )

        if not output.exists():
            raise RuntimeError(
                "تم تنفيذ عملية الفيديو لكن الملف النهائي غير موجود."
            )

        print(
            "🎥 FINAL VIDEO:",
            output
        )

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        await update.message.reply_text(
            "✅ خلص الرندر!\n"
            "📤 جاري إرسال الفيديو..."
        )

        with open(
            output,
            "rb"
        ) as video_file:

            await update.message.reply_video(
                video=video_file,
                caption=(
                    f"🎬 {plan.title}\n"
                    f"⏱️ {plan.duration:.1f} ثانية\n"
                    f"🎞️ {len(plan.shots)} لقطات"
                ),
                supports_streaming=True,
            )

        # ----------------------------------------------------
        # MEMORY
        # ----------------------------------------------------

        conversation_memory.add(
            user_id,
            "user",
            "[طلب إنشاء فيديو]\n" + text
        )

        conversation_memory.add(
            user_id,
            "assistant",
            f"[تم إنشاء فيديو سينمائي]\n"
            f"Title: {plan.title}\n"
            f"Duration: {plan.duration:.1f}s\n"
            f"Shots: {len(plan.shots)}"
        )

    except Exception as e:
        traceback.print_exc()

        await update.message.reply_text(
            "❌ حدث خطأ أثناء إنشاء الفيديو:\n\n"
            f"{type(e).__name__}: {e}"
        )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        await update.message.reply_text(
            "🎥 تم استلام الفيديو.\n"
            "⏳ سأستخرج الصوت منه ثم أحوله إلى نص.\n"
            "هذا قد يستغرق وقتاً حسب طول المحاضرة."
        )

        video = update.message.video

        file = await video.get_file()

        video_dir = DATA_DIR / "videos"
        video_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        video_path = (
            video_dir
            / f"{user_id}_{video.file_unique_id}.mp4"
        )

        await file.download_to_drive(
            custom_path=str(video_path),
            read_timeout=900,
            write_timeout=900,
            connect_timeout=120,
            pool_timeout=900,
        )

        await update.message.reply_text(
            "🔊 جاري استخراج الصوت من الفيديو..."
        )

        wav_file = (
            video_dir
            / f"{user_id}_{video.file_unique_id}.wav"
        )

        await asyncio.to_thread(
            extract_audio,
            video_path,
            wav_file
        )

        await update.message.reply_text(
            "📝 الصوت جاهز.\n"
            "🧠 جاري تفريغ المحاضرة باستخدام Whisper..."
        )

        transcript = await asyncio.to_thread(
            transcribe_with_whisper,
            wav_file
        )

        if not transcript:
            await update.message.reply_text(
                "❌ لم أستطع استخراج الكلام من الفيديو."
            )
            return

        await update.message.reply_text(
            "✅ تم تفريغ المحاضرة.\n"
            "📚 جاري إعداد الملخص..."
        )

        prompt = (
            "أنت أستاذ رياضيات.\n"
            "لديك تفريغ لمحاضرة من فيديو.\n\n"
            "قم بما يلي:\n"
            "1. لخص المحاضرة.\n"
            "2. استخرج أهم الأفكار.\n"
            "3. استخرج القوانين والمعادلات.\n"
            "4. اشرح المفاهيم المهمة ببساطة.\n"
            "5. استخرج الأمثلة الرياضية إن وجدت.\n"
            "6. إذا كان هناك أخطاء واضحة في التفريغ "
            "فحاول تصحيحها اعتماداً على السياق.\n\n"
            f"تفريغ المحاضرة:\n{transcript}"
        )

        answer = await asyncio.to_thread(
            ask_gemini,
            prompt,
            conversation_memory.get(user_id),
            persistent_memory.get_all(user_id)
        )

        conversation_memory.add(
            user_id,
            "user",
            "[محاضرة فيديو]\n" + transcript
        )

        conversation_memory.add(
            user_id,
            "assistant",
            answer
        )

        await send_long_message(
            update,
            "📚 ملخص المحاضرة:\n\n" + answer
        )

    except Exception as e:
        traceback.print_exc()

        await update.message.reply_text(
            f"❌ حدث خطأ أثناء معالجة الفيديو:\n{e}"
        )


# ============================================================
# ERROR HANDLER
# ============================================================

# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update, context):
    print("\n========== APPLICATION ERROR ==========", flush=True)

    try:
        print(
            "ERROR TYPE:",
            type(context.error).__name__,
            flush=True,
        )
        print(
            "ERROR:",
            repr(context.error),
            flush=True,
        )
        traceback.print_exception(
            type(context.error),
            context.error,
            context.error.__traceback__,
        )
    except Exception as handler_error:
        print(
            "ERROR HANDLER FAILED:",
            repr(handler_error),
            flush=True,
        )


# ============================================================
# MAIN
# ============================================================

def main():
    if not TOKEN:
        print(
            "❌ TELEGRAM_TOKEN غير موجود داخل ملف .env"
        )
        return

    print(
        "Whisper binary:",
        WHISPER_BIN
    )

    print(
        "Whisper model:",
        WHISPER_MODEL
    )

    print(
        "Whisper exists:",
        WHISPER_BIN.exists()
    )

    print(
        "Model exists:",
        WHISPER_MODEL.exists()
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^[1-5]$"),
            handle_pdf_action
        )
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^/pronounce\b"),
            handle_pronunciation
        )
    )

    # الصور
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    # الصوت
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            handle_voice
        )
    )

    # الفيديو
    app.add_handler(
        MessageHandler(
            filters.VIDEO | filters.VIDEO_NOTE,
            handle_video
        )
    )

    # الملفات
    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            handle_document
        )
    )

    # النص
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "🚀 MathProfessor-Bot Started"
    )

    app.run_polling()





# ============================================================
# OFFICIAL PDF TABLE OF CONTENTS
# ============================================================


# ============================================================
# OFFICIAL PDF TABLE OF CONTENTS
# ============================================================

def add_official_toc_to_pdf(pdf_path, user_id):
    """
    إنشاء صفحة فهرس رسمية وإضافتها كأول صفحة في ملف PDF.
    يعتمد على Document Intelligence إذا كان متاحًا.
    """

    from pathlib import Path
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from pypdf import PdfReader, PdfWriter

    pdf_path = Path(pdf_path)

    # --------------------------------------------------------
    # العثور على RAG الخاص بالمستخدم
    # --------------------------------------------------------
    try:
        rag = persistent_rag

        document = rag.get_document(user_id)

        if not document:
            print("⚠️ لا يوجد document في RAG لإنشاء الفهرس")
            return pdf_path

        content = document.get("content", "")
        filename = document.get("file_info", {}).get(
            "filename",
            pdf_path.name,
        )

    except Exception as e:
        print("⚠️ TOC RAG ERROR:", repr(e))
        return pdf_path

    # --------------------------------------------------------
    # بناء Document Intelligence
    # --------------------------------------------------------
    try:
        from core.document_intelligence.document import parse_document
        from core.document_intelligence.structure import (
            DocumentStructureAnalyzer,
        )
        from core.document_intelligence.index import DocumentIndex

        parsed_document = parse_document(
            content,
            filename=filename,
        )

        structure = DocumentStructureAnalyzer().analyze(
            parsed_document
        )

        index = DocumentIndex(
            parsed_document,
            structure,
        )

        toc_text = index.table_of_contents()

    except Exception as e:
        print("⚠️ TOC DOCUMENT INTELLIGENCE ERROR:", repr(e))
        return pdf_path

    if not toc_text.strip():
        print("⚠️ لم يتم العثور على دروس لإنشاء الفهرس")
        return pdf_path

    # --------------------------------------------------------
    # الخط العربي
    # --------------------------------------------------------
    font_name = "Helvetica"

    font_candidates = [
        "/system/fonts/NotoNaskhArabic-Regular.ttf",
        "/system/fonts/NotoSansArabic-Regular.ttf",
        "/system/fonts/NotoSansArabic-Regular.ttf",
    ]

    for font_path in font_candidates:
        try:
            if Path(font_path).exists():
                pdfmetrics.registerFont(
                    TTFont(
                        "ArabicTOC",
                        font_path,
                    )
                )
                font_name = "ArabicTOC"
                break
        except Exception:
            pass

    # --------------------------------------------------------
    # إنشاء صفحة الفهرس
    # --------------------------------------------------------
    buffer = BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=A4,
    )

    width, height = A4

    # العنوان
    c.setFont(
        font_name,
        22,
    )

    c.drawCentredString(
        width / 2,
        height - 60,
        "فهرس المحتويات",
    )

    # خط أسفل العنوان
    c.line(
        50,
        height - 75,
        width - 50,
        height - 75,
    )

    # --------------------------------------------------------
    # رسم الفهرس
    # --------------------------------------------------------
    y = height - 110

    c.setFont(
        font_name,
        12,
    )

    for raw_line in toc_text.splitlines():

        line = raw_line.strip()

        if not line:
            y -= 8
            continue

        # صفحة جديدة إذا امتلأت الصفحة
        if y < 60:
            c.showPage()

            c.setFont(
                font_name,
                12,
            )

            y = height - 50

        # الوحدات
        if line.startswith("📚"):
            c.setFont(
                font_name,
                14,
            )

            c.drawRightString(
                width - 50,
                y,
                line.replace("📚", "").strip(),
            )

            y -= 25

            c.setFont(
                font_name,
                12,
            )

        else:
            # إزالة الرموز التي قد لا يدعمها الخط
            clean_line = (
                line
                .replace("📚", "")
                .replace("—", " - ")
            )

            c.drawRightString(
                width - 65,
                y,
                clean_line,
            )

            y -= 20

    c.save()

    buffer.seek(0)

    # --------------------------------------------------------
    # دمج صفحة الفهرس مع الـPDF الأصلي
    # --------------------------------------------------------
    original_reader = PdfReader(
        str(pdf_path)
    )

    toc_reader = PdfReader(
        buffer
    )

    writer = PdfWriter()

    # الفهرس أولاً
    for page in toc_reader.pages:
        writer.add_page(page)

    # ثم صفحات الكتاب الأصلية
    for page in original_reader.pages:
        writer.add_page(page)

    # ملف مؤقت
    temp_path = pdf_path.with_suffix(
        ".with_toc.pdf"
    )

    with open(
        temp_path,
        "wb",
    ) as f:
        writer.write(f)

    # استبدال الملف الأصلي
    temp_path.replace(pdf_path)

    print(
        "✅ OFFICIAL PDF TOC ADDED:",
        pdf_path,
    )

    return pdf_path

if __name__ == "__main__":
    main()
