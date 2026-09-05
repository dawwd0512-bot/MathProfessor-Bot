import asyncio
import subprocess
from pathlib import Path

from telegram import Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from core.agent_v2 import AgentV2
from phone_agent.commands import execute as execute_phone_command
from core.config import Config
from core.files.storage import save_file
from core.files.video_evidence import build_video_evidence
from core.knowledge.retrieval.document_reader import DocumentReader
from core.vision.image import analyze_image
from core.voice.tts import text_to_speech


class TelegramBot:

    def __init__(self):

        self.agent = AgentV2()

        self.token = Config.TELEGRAM_BOT_TOKEN

        self.document_reader = DocumentReader()

        # آخر ملف لكل مستخدم.
        # يسمح للمستخدم بإرسال الملف مرة واحدة ثم طرح عدة أسئلة عليه.
        self.user_files = {}


    async def start_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        await update.message.reply_text(
            "⚡ MathProfessor Online\n"
            "أرسل ملفاً أو اكتب سؤالك مباشرة."
        )


    async def handle_document(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user_id = str(
            update.effective_user.id
        )

        document = update.message.document

        filename = document.file_name or "uploaded_file"

        allowed = (
            ".pdf",
            ".docx",
            ".txt",
            ".md"
        )

        if not filename.lower().endswith(allowed):

            await update.message.reply_text(
                "❌ نوع الملف غير مدعوم.\n"
                "الأنواع المدعومة: PDF, DOCX, TXT, MD"
            )

            return

        try:

            telegram_file = await document.get_file()

            content = await telegram_file.download_as_bytearray()

            path = save_file(
                user_id,
                filename,
                bytes(content)
            )

            result = self.document_reader.read(path)

            if not result.get("success"):

                await update.message.reply_text(
                    "❌ تم استلام الملف لكن تعذر قراءته:\n"
                    + str(result.get("error"))
                )

                return

            file_context = result.get(
                "content",
                ""
            )

            self.user_files[user_id] = {
                "path": path,
                "filename": filename,
                "content": file_context
            }

            await update.message.reply_text(
                "✅ تم استلام الملف بنجاح.\n\n"
                f"📄 {filename}\n\n"
                "الآن اكتب سؤالك عنه، مثل:\n"
                "• اشرح هذا الفصل\n"
                "• ما معنى هذه النظرية؟\n"
                "• حل المثال الموجود في الملف\n"
                "• لخص لي هذا الجزء"
            )

        except Exception as e:

            await update.message.reply_text(
                "❌ حدث خطأ أثناء معالجة الملف:\n"
                + str(e)
            )



    async def handle_video(self, update, context):
        try:
            user_id = str(update.effective_user.id)

            await update.message.reply_text(
                "🎬 تم استلام الفيديو.\n"
                "⏳ جاري استخراج الصوت واللقطات وبناء فهم الفيديو..."
            )

            video = update.message.video

            media_dir = (
                Path("data/uploads")
                / user_id
                / "video"
            )
            media_dir.mkdir(parents=True, exist_ok=True)

            video_path = (
                media_dir
                / f"{video.file_unique_id}.mp4"
            )

            await (await video.get_file()).download_to_drive(
                custom_path=str(video_path),
                read_timeout=600,
                write_timeout=600,
                connect_timeout=60,
                pool_timeout=600,
            )

            wav_path = media_dir / f"{video.file_unique_id}.wav"

            await asyncio.to_thread(
                subprocess.run,
                [
                    "ffmpeg",
                    "-y",
                    "-i", str(video_path),
                    "-vn",
                    "-ar", "16000",
                    "-ac", "1",
                    str(wav_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            evidence_dir = (
                media_dir
                / f"{video.file_unique_id}_evidence"
            )

            evidence = await asyncio.to_thread(
                build_video_evidence,
                str(video_path),
                str(wav_path),
                str(evidence_dir),
                12,
            )

            transcript = evidence.get("transcript", [])
            timeline = evidence.get("timeline", [])

            if not transcript and not timeline:
                await update.message.reply_text(
                    "❌ لم أستطع استخراج معلومات مفيدة من الفيديو."
                )
                return

            transcript_text = "\n".join(
                f"[{float(item['start']):.2f}s → "
                f"{float(item['end']):.2f}s] "
                f"{item.get('text', '')}"
                for item in transcript
            )

            timeline_text_parts = []

            for item in timeline:
                lines = [
                    f"[{float(item['start']):.2f}s → "
                    f"{float(item['end']):.2f}s]",
                    f"الكلام: {item.get('text', '')}",
                ]

                for visual in item.get("visuals", []):
                    screen_text = (
                        visual.get("screen_text") or ""
                    ).strip()

                    lines.append(
                        f"لقطة عند "
                        f"{float(visual['timestamp']):.2f}s"
                    )

                    if screen_text:
                        lines.append(
                            f"النص الظاهر: {screen_text}"
                        )

                timeline_text_parts.append(
                    "\n".join(lines)
                )

            timeline_text = "\n\n".join(
                timeline_text_parts
            )

            caption = update.message.caption or ""

            prompt = f"""
أنت محلل فيديو رياضي/تعليمي يعتمد فقط على الأدلة المستخرجة من الفيديو.

مهم جدًا:
- لا تخترع أي معلومة غير موجودة في الأدلة.
- إذا لم توجد الإجابة في الفيديو، قل بوضوح:
  "هذه المعلومة غير موجودة في الفيديو."
- استخدم التوقيتات عند الإجابة عن أسئلة "متى؟".
- فرّق بين الكلام المنطوق والنص الظاهر على الشاشة.
- إذا كان السؤال عن مسألة رياضية، استخدم الأرقام والمعادلات الظاهرة أو المنطوقة فقط.
- لا تفترض أرقامًا غير موجودة.
- إذا كانت الأدلة غير كافية، صرّح بذلك بدل التخمين.

طلب المستخدم:
{caption or "لخص الفيديو واذكر أهم القوانين والأمثلة."}

TRANSCRIPT:
{transcript_text}

TIMELINE / VISUAL EVIDENCE:
{timeline_text}
"""

            await update.message.reply_text(
                "🧠 تم استخراج الأدلة من الفيديو.\n"
                "🔎 جاري تحليلها..."
            )

            response = await asyncio.to_thread(
                self.agent.chat,
                prompt,
                user_id=user_id,
                file_context=None
            )

            if isinstance(response, dict):
                text = response.get(
                    "response",
                    response
                )

                if isinstance(text, dict):
                    results = text.get(
                        "results",
                        []
                    )

                    if results:
                        text = results[-1].get(
                            "output",
                            results[-1]
                        )
            else:
                text = response

            await update.message.reply_text(
                str(text)
            )

        except Exception as e:
            print("VIDEO ERROR:", repr(e))
            await update.message.reply_text(
                f"❌ حدث خطأ أثناء معالجة الفيديو:\n{e}"
            )


    async def handle_photo(self, update, context):
        try:
            user_id = str(update.effective_user.id)
            await update.message.reply_text("🖼️ جاري تحليل الصورة...")

            photo = update.message.photo[-1]
            telegram_file = await photo.get_file()

            media_dir = Path("data/uploads") / user_id / "images"
            media_dir.mkdir(parents=True, exist_ok=True)

            image_path = media_dir / f"{photo.file_unique_id}.jpg"

            await telegram_file.download_to_drive(
                custom_path=str(image_path),
                read_timeout=120,
                write_timeout=120,
                connect_timeout=60,
                pool_timeout=120,
            )

            caption = update.message.caption or ""

            prompt = (
                "اقرأ الصورة كاملة بدقة. "
                "إذا كانت تحتوي على عدة أسئلة أو تمارين، حل جميع الأسئلة الظاهرة "
                "ولا تتوقف عند أول سؤال.\n\n"
                f"طلب المستخدم: {caption}"
            )

            answer = await asyncio.to_thread(
                analyze_image,
                str(image_path),
                prompt
            )

            await update.message.reply_text(str(answer))

        except Exception as e:
            print("PHOTO ERROR:", repr(e))
            await update.message.reply_text(
                f"❌ حدث خطأ أثناء تحليل الصورة:\n{e}"
            )


    async def handle_voice(self, update, context):
        try:
            user_id = str(update.effective_user.id)

            await update.message.reply_text(
                "🎤 جاري تحويل التسجيل إلى نص..."
            )

            voice = update.message.voice
            telegram_file = await voice.get_file()

            media_dir = Path("data/uploads") / user_id / "voice"
            media_dir.mkdir(parents=True, exist_ok=True)

            ogg = media_dir / f"{voice.file_unique_id}.ogg"
            wav = media_dir / f"{voice.file_unique_id}.wav"

            await telegram_file.download_to_drive(
                custom_path=str(ogg),
                read_timeout=300,
                write_timeout=300,
                connect_timeout=60,
                pool_timeout=300,
            )

            await asyncio.to_thread(
                subprocess.run,
                [
                    "ffmpeg", "-y",
                    "-i", str(ogg),
                    "-ar", "16000",
                    "-ac", "1",
                    str(wav)
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )

            root = Path(__file__).resolve().parents[2]

            whisper = root / "third_party/whisper.cpp/build/bin/whisper-cli"
            model = root / "third_party/whisper.cpp/models/ggml-tiny-q5_1.bin"

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    str(whisper),
                    "-m", str(model),
                    "-f", str(wav),
                    "-nt"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            lines = []

            for line in result.stdout.splitlines():
                line = line.strip()

                if line.startswith("[") and "]" in line:
                    text = line.split("]", 1)[1].strip()

                    if text:
                        lines.append(text)

            transcript = " ".join(lines).strip()

            if not transcript:
                await update.message.reply_text(
                    "❌ لم أستطع استخراج الكلام من التسجيل."
                )
                return

            await update.message.reply_text(
                "📝 تم تفريغ التسجيل.\n🧠 جاري التحليل..."
            )

            response = self.agent.chat(
                transcript,
                user_id=user_id,
                file_context=None
            )

            if isinstance(response, dict):
                text = response.get("response", response)

                if isinstance(text, dict):
                    results = text.get("results", [])

                    if results:
                        text = results[-1].get(
                            "output",
                            results[-1]
                        )
            else:
                text = response

            await update.message.reply_text(str(text))

        except Exception as e:
            print("VOICE ERROR:", repr(e))
            await update.message.reply_text(
                f"❌ حدث خطأ أثناء معالجة الصوت:\n{e}"
            )


    async def handle_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user_id = str(
            update.effective_user.id
        )

        message = update.message.text

        file_context = None

        if user_id in self.user_files:

            file_context = self.user_files[user_id].get(
                "content"
            )

        # ============================================================
        # PHONE AGENT
        # أوامر الهاتف المستقلة لا تمر عبر AgentV2.
        # ============================================================
        if message.strip() in ("يوتيوب", "افتح يوتيوب") or message.strip().startswith(("افتح http://", "افتح https://", "open http://", "open https://")):
            try:
                phone_result = execute_phone_command(message)
                await update.message.reply_text(phone_result)
                return
            except Exception as e:
                print("PHONE AGENT ERROR:", repr(e))

        response = self.agent.chat(
            message,
            user_id=user_id,
            file_context=file_context
        )

        # ============================================================
        # GRAPH RESULT
        # ============================================================
        # إذا أنشأ AgentV2 رسمًا بيانيًا، نبحث عن graph_path
        # داخل النتيجة كاملة، ثم نرسل ملف PNG كصورة فعلية إلى Telegram.
        # ============================================================

        graph_path = None

        def _find_graph_path(value):
            if isinstance(value, dict):

                if value.get("graph_path"):
                    return value.get("graph_path")

                for child in value.values():
                    found = _find_graph_path(child)

                    if found:
                        return found

            elif isinstance(value, (list, tuple)):

                for child in value:
                    found = _find_graph_path(child)

                    if found:
                        return found

            return None

        if isinstance(response, dict):

            graph_path = _find_graph_path(response)

            # --------------------------------------------------------
            # fallback: بعض النتائج قد تضع المسار داخل response
            # --------------------------------------------------------
            if not graph_path:

                response_path = response.get("response")

                if isinstance(response_path, str):

                    candidate = response_path.strip()

                    if (
                        "generatedimages" in candidate
                        and "telegramgraph" in candidate
                    ):
                        candidate = candidate.replace(
                            "generatedimages",
                            "generated_images"
                        )

                        candidate = candidate.replace(
                            "telegramgraph",
                            "telegram_graph"
                        )

                        graph_path = candidate

        if graph_path:

            graph_path = Path(str(graph_path))

            # إذا كان الرسم SVG قديمًا، ابحث عن PNG المقابل له.
            if graph_path.suffix.lower() == ".svg":

                png_path = graph_path.with_suffix(".png")

                if png_path.exists():
                    graph_path = png_path

            if graph_path.exists():

                print(
                    "📈 GRAPH PNG FOUND:",
                    graph_path
                )

                try:

                    with open(graph_path, "rb") as graph_file:

                        await update.message.reply_photo(
                            photo=graph_file,
                            caption="📈 تم إنشاء الرسم البياني."
                        )

                    print("✅ GRAPH PNG SENT TO TELEGRAM")

                    return

                except Exception as graph_send_error:

                    print(
                        "❌ GRAPH PNG SEND ERROR:",
                        repr(graph_send_error)
                    )

        # ============================================================
        # NORMAL RESPONSE
        # ============================================================

        if isinstance(response, dict):

            text = response.get(
                "response",
                response
            )

            if isinstance(text, dict):

                results = text.get(
                    "results",
                    []
                )

                if results:

                    text = results[-1].get(
                        "output",
                        results[-1]
                    )

        else:

            text = response

        # ============================================================
        # GRAPH RESULT
        # ============================================================
        # AgentV2 يضع مسار الرسم داخل response["raw"].
        # يجب إرسال الملف فعليًا إلى Telegram بدل إرسال المسار كنص.
        # ============================================================

        graph_path = None

        def _find_graph_path(value):
            if isinstance(value, dict):
                if value.get("graph_path"):
                    return value.get("graph_path")

                for child in value.values():
                    found = _find_graph_path(child)
                    if found:
                        return found

            elif isinstance(value, (list, tuple)):
                for child in value:
                    found = _find_graph_path(child)
                    if found:
                        return found

            return None

        if isinstance(response, dict):
            graph_path = _find_graph_path(response)

        if graph_path:
            graph_path = Path(str(graph_path))

            if graph_path.exists():
                try:
                    print("📈 GRAPH PATH FOUND:", graph_path)

                    suffix = graph_path.suffix.lower()

                    with open(graph_path, "rb") as graph_file:
                        if suffix in (".jpg", ".jpeg", ".png", ".webp"):
                            await update.message.reply_photo(
                                photo=graph_file,
                                caption="📈 تم إنشاء الرسم البياني."
                            )
                        else:
                            await update.message.reply_document(
                                document=graph_file,
                                filename=graph_path.name,
                                caption="📈 تم إنشاء الرسم البياني."
                            )

                    print("✅ GRAPH SENT TO TELEGRAM")
                    return

                except Exception as graph_send_error:
                    print(
                        "❌ GRAPH SEND ERROR:",
                        repr(graph_send_error)
                    )

        # ============================================================
        # PRONUNCIATION / TTS
        # ============================================================
        # إذا كان AgentV2 قد حدد الطلب كنطق، أرسل الصوت مباشرة.
        # باقي الرسائل تبقى على مسار reply_text القديم.
        # ============================================================

        pronunciation_text = None

        if isinstance(response, dict):
            pronunciation_text = response.get("pronunciation")

        if pronunciation_text:
            try:
                voice_dir = (
                    Path("data/uploads")
                    / user_id
                    / "voice"
                )

                voice_dir.mkdir(
                    parents=True,
                    exist_ok=True
                )

                audio_path = (
                    voice_dir
                    / "pronunciation.mp3"
                )

                await text_to_speech(
                    str(pronunciation_text),
                    str(audio_path)
                )

                with open(audio_path, "rb") as audio:
                    await update.message.reply_voice(
                        voice=audio
                    )

                return

            except Exception as e:
                print("PRONUNCIATION TTS ERROR:", repr(e))

                # إذا فشل TTS لا نكسر البوت،
                # بل نرجع النص كخطة احتياطية.
                await update.message.reply_text(
                    str(pronunciation_text)
                )

                return

        await update.message.reply_text(
            str(text)
        )


    def run(self):

        if not self.token:

            raise ValueError(
                "TELEGRAM_BOT_TOKEN missing"
            )

        request = HTTPXRequest(
            connect_timeout=30,
            read_timeout=90,
            write_timeout=90,
            pool_timeout=30,
        )

        app = (
            Application
            .builder()
            .token(self.token)
            .request(request)
            .build()
        )

        app.add_handler(
            CommandHandler(
                "start",
                self.start_command
            )
        )

        # الفيديو
        app.add_handler(
            MessageHandler(
                filters.VIDEO,
                self.handle_video
            )
        )

        # الصور والصوت
        app.add_handler(
            MessageHandler(
                filters.PHOTO,
                self.handle_photo
            )
        )

        app.add_handler(
            MessageHandler(
                filters.VOICE,
                self.handle_voice
            )
        )

        # الملفات أولاً
        app.add_handler(
            MessageHandler(
                filters.Document.ALL,
                self.handle_document
            )
        )

        # الرسائل النصية
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_message
            )
        )

        print(
            "⚡ MathProfessor Telegram Bot Running"
        )

        app.run_polling()


if __name__ == "__main__":

    bot = TelegramBot()

    bot.run()
