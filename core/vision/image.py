import os
import base64
import mimetypes
import requests

from dotenv import load_dotenv

load_dotenv()


API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)


MODEL = os.getenv(
    "GEMINI_VISION_MODEL",
    "gemini-3.1-flash-lite"
)


def extract_math_text_from_image(image_path: str, user_request: str = "") -> str:
    """
    Vision OCR/transcription فقط.
    لا تحل المسألة ولا تشرحها.
    الهدف هو استخراج النص الرياضي من الصورة بدقة ثم تمريره إلى AgentV2.
    """

    if not API_KEY:
        return "❌ GEMINI_API_KEY غير موجود في ملف .env"

    if not os.path.exists(image_path):
        return "❌ الصورة غير موجودة."

    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"

    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(
                f.read()
            ).decode("utf-8")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{MODEL}:generateContent?key={API_KEY}"
        )

        extraction_prompt = f"""
أنت الآن تعمل كقارئ صور رياضية فقط داخل MathProfessor-Bot.

مهمتك الوحيدة:
استخراج النص الرياضي الظاهر في الصورة بدقة شديدة.

ممنوع عليك حل أي مسألة.
ممنوع عليك إعطاء نتيجة نهائية.
ممنوع عليك اختراع أي رقم أو رمز.
ممنوع عليك شرح الحل.

يجب:
1. قراءة الصورة كاملة.
2. استخراج جميع الأسئلة والتمارين الظاهرة.
3. الحفاظ على الأرقام والإشارات والأقواس والكسور والأسس والجذور.
4. الحفاظ على حدود التكامل.
5. الحفاظ على أسماء الدوال مثل ln وlog وsin وcos.
6. تحويل الرموز إلى نص واضح يمكن لـ Math Engine قراءته.
7. إذا كان هناك سؤال واحد فقط، أخرج ذلك السؤال كاملًا.
8. إذا كانت هناك عدة أسئلة، أخرجها كلها بالترتيب.
9. إذا كان جزء غير واضح، اكتب [غير واضح] بدل التخمين.
10. لا تضف أي حل أو تفسير.

طلب المستخدم:
{user_request}

أخرج فقط النص المستخرج من الصورة.
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": extraction_prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192
            }
        }

        response = requests.post(
            url,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return "❌ Gemini لم يرجع نصًا من الصورة."

        parts = candidates[0].get(
            "content",
            {}
        ).get(
            "parts",
            []
        )

        text = "".join(
            part.get("text", "")
            for part in parts
            if "text" in part
        )

        return (
            text.strip()
            or "❌ لم يتم استخراج النص من الصورة."
        )

    except requests.RequestException as e:
        return (
            "❌ خطأ في الاتصال بـ Gemini أثناء قراءة الصورة: "
            f"{e}"
        )
    except Exception as e:
        return (
            "❌ خطأ أثناء استخراج النص من الصورة: "
            f"{e}"
        )



def analyze_image(image_path: str, prompt: str) -> str:
    """
    Image -> Gemini Vision extraction -> Math Engine verification -> final answer.

    Gemini is used for visual understanding/extraction.
    Math Engine is authoritative for machine-solvable mathematics.
    """

    if not API_KEY:
        return "❌ GEMINI_API_KEY غير موجود في ملف .env"

    if not os.path.exists(image_path):
        return "❌ الصورة غير موجودة."

    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"

    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(
                f.read()
            ).decode("utf-8")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{MODEL}:generateContent?key={API_KEY}"
        )

        # ============================================================
        # PHASE 1 — VISION EXTRACTION ONLY
        # Gemini must READ the image, not solve the mathematics.
        # ============================================================

        extraction_prompt = f"""
أنت الآن في مرحلة استخراج البيانات من صورة رياضيات فقط.

مهمتك الأساسية:
اقرأ الصورة بدقة شديدة واستخرج جميع الأسئلة والمعادلات والأرقام
كما تظهر في الصورة.

لا تحل أي سؤال.
لا تعطِ نتيجة نهائية.
لا تخمّن أي رقم أو رمز غير واضح.

قواعد إلزامية:
1. اقرأ الصورة كاملة.
2. حدّد جميع أرقام الأسئلة الظاهرة.
3. انسخ كل معادلة رياضية بدقة.
4. حافظ على الحدود العليا والسفلى للتكامل.
5. حافظ على الأقواس والأسس والجذور والكسور والإشارات.
6. إذا وجدت تكاملًا، اكتبه بصيغة واضحة قابلة للمعالجة.
7. إذا وجدت مشتقة، اكتب الدالة كاملة.
8. إذا وجدت معادلة، اكتب طرفيها كاملين.
9. إذا كان هناك أكثر من سؤال، استخرجها كلها.
10. إذا كان جزء غير واضح، اكتب [غير واضح] بدل التخمين.

أخرج النص المستخرج فقط، بدون حل.

طلب المستخدم:
{prompt}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": extraction_prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192
            }
        }

        response = requests.post(
            url,
            json=payload,
            timeout=180
        )

        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return "❌ Gemini لم يرجع نصًا من الصورة."

        parts = candidates[0].get(
            "content",
            {}
        ).get(
            "parts",
            []
        )

        extracted_text = "".join(
            part.get("text", "")
            for part in parts
            if "text" in part
        ).strip()

        if not extracted_text:
            return "❌ لم أستطع استخراج المسائل من الصورة."

        # ============================================================
        # PHASE 2 — MATH ENGINE
        # Try every extracted line/question through the authoritative
        # Super Math engine.
        # ============================================================

        try:
            from core.ai.math_engine import (
                solve_super_math,
                format_result,
            )

            verified_results = []
            unresolved = []

            # Split conservatively by question markers.
            import re

            chunks = re.split(
                r'(?=(?:السؤال|سؤال|question)\s*[\d١٢٣٤٥٦٧٨٩٠]+)',
                extracted_text,
                flags=re.IGNORECASE
            )

            chunks = [
                c.strip()
                for c in chunks
                if c.strip()
            ]

            if not chunks:
                chunks = [extracted_text]

            for chunk in chunks:
                # Remove only obvious question labels before sending
                # the mathematical content to the engine.
                clean_chunk = re.sub(
                    r'^(?:السؤال|سؤال|question)\s*[\d١٢٣٤٥٦٧٨٩٠]+\s*:?\s*',
                    '',
                    chunk,
                    flags=re.IGNORECASE
                ).strip()

                if not clean_chunk:
                    continue

                try:
                    # ====================================================
                    # GRAPH / VISUAL QUESTION GUARD
                    # ====================================================
                    # Do NOT send graph-analysis questions such as
                    # y = f(x), domains, ranges, continuity, limits
                    # read from a graph, etc. to SymPy.
                    #
                    # These require visual interpretation and must remain
                    # with Gemini Vision in the final explanation phase.
                    # ====================================================

                    graph_visual_patterns = (
                        "y = f(x)",
                        "y=f(x)",
                        "f(x)",
                        "من الرسم",
                        "الرسم البياني",
                        "الرسم",
                        "المجال",
                        "المدى",
                        "متصلة",
                        "الاتصال",
                        "نقطة مفتوحة",
                        "نقطة مغلقة",
                        "graph",
                        "domain",
                        "range",
                        "continuous",
                        "continuity",
                        "open point",
                        "closed point",
                    )

                    lower_chunk = clean_chunk.lower()

                    is_graph_visual = any(
                        pattern.lower() in lower_chunk
                        for pattern in graph_visual_patterns
                    )

                    if is_graph_visual:
                        print(
                            "IMAGE ROUTING: visual/graph question -> Gemini Vision"
                        )
                        unresolved.append(chunk)
                        continue

                    # ====================================================
                    # MATH ENGINE
                    # Only genuinely machine-solvable mathematics reaches
                    # the authoritative Super Math engine.
                    # ====================================================

                    math_result = solve_super_math(clean_chunk)

                    if (
                        isinstance(math_result, dict)
                        and math_result.get("verified") is True
                        and math_result.get("result") is not None
                    ):
                        verified_results.append(
                            (
                                chunk,
                                math_result,
                                format_result(math_result)
                            )
                        )
                    else:
                        unresolved.append(chunk)

                except Exception as e:
                    print(
                        "IMAGE MATH ROUTING ERROR:",
                        repr(e)
                    )
                    unresolved.append(chunk)

            # ========================================================
            # PHASE 3 — VERIFIED MATH ANSWER
            # If Math Engine solved something, return its verified
            # mathematical result instead of allowing Gemini to invent.
            # ========================================================

            if verified_results and not unresolved:
                output = []

                for index, (original, result, formatted) in enumerate(
                    verified_results,
                    start=1
                ):
                    output.append(
                        f"السؤال {index}:\n"
                        f"{original}\n\n"
                        f"النتيجة المحققة:\n"
                        f"{formatted}"
                    )

                return "\n\n".join(output)

            # ========================================================
            # PHASE 4 — MIXED IMAGE
            # Some questions may be mathematical and others may depend
            # on graphs/visual interpretation.
            #
            # Give Gemini the extracted text plus verified Math Engine
            # results and explicitly forbid contradicting them.
            # ========================================================

            verified_context = []

            for original, result, formatted in verified_results:
                verified_context.append(
                    "المسألة المستخرجة:\n"
                    f"{original}\n"
                    "نتيجة Math Engine الموثقة:\n"
                    f"{formatted}"
                )

            verification_block = "\n\n".join(
                verified_context
            )

        except Exception as math_error:
            print(
                "IMAGE MATH ENGINE ERROR:",
                repr(math_error)
            )
            verification_block = ""

        # ============================================================
        # PHASE 5 — FINAL EXPLANATION
        # Gemini may explain visual/non-computable questions, but it
        # must respect verified Math Engine results.
        # ============================================================

        final_prompt = f"""
أنت MathProfessor-Bot.

تمت قراءة الصورة واستخراج محتواها في مرحلة سابقة.

النص المستخرج من الصورة:
========================
{extracted_text}
========================

نتائج Math Engine الموثقة:
========================
{verification_block or "لا توجد نتيجة آلية موثقة."}
========================

مهم جدًا:

1. لا تخترع أي رقم أو رمز غير موجود في النص المستخرج.
2. إذا كانت هناك نتيجة من Math Engine وعليها verified=True،
   فهي المرجع الرياضي الموثوق ولا يجوز تغييرها.
3. إذا لم توجد نتيجة موثقة لمسألة تعتمد على رسم بياني أو تفسير بصري،
   حلل الرسم الموجود في الصورة بحذر.
4. إذا كان شيء غير واضح، قل إنه غير واضح بدل التخمين.
5. أجب عن جميع الأسئلة الظاهرة.
6. اجعل تنسيق الإجابة مريحًا للعين ومناسبًا لشاشة الهاتف.
7. لا تستخدم قالبًا ثابتًا من نوع "السؤال / الحل / القانون / الإجابة"
   في كل مرة.
8. ابدأ مباشرة بالمسألة أو الحل، واستخدم عناوين قصيرة فقط عندما تساعد
   على تنظيم الإجابة.
9. اعرض العمليات والمعادلات الرياضية في أسطر منفصلة وواضحة.
10. اشرح الخطوات الضرورية فقط، وتجنب الحشو والتكرار.
11. ضع النتيجة النهائية في نهاية كل مسألة بشكل واضح، ويفضل إبرازها
    بصيغة رياضية مناسبة عندما يكون ذلك مفيدًا.
12. إذا كان هناك قانون أو طريقة مهمة للحل، اذكرها باختصار داخل الشرح
    بدل إنشاء قسم منفصل دائمًا.
13. لا تدّعِ أن نتيجة غير موثقة تم التحقق منها.
14. لا تستخدم نتيجة سابقة من ذاكرتك بدل الصورة الحالية.
15. إذا كانت المسألة تكاملًا صعبًا ولها نتيجة موثقة من Math Engine،
    استخدمها كما هي.
16. إذا احتوت الصورة على أسئلة تعتمد على الرسم البياني، استخدم
    المعلومات البصرية الموجودة في الصورة نفسها.

اكتب الإجابة بالعربية، بشكل أكاديمي واضح، مختصر قدر الإمكان،
ومريح جدًا للقراءة على الهاتف.

  مهم جدًا لتنسيق Telegram:
  - الإجابة يجب أن تكون بالعربية.
  - ممنوع استخدام علامات LaTeX الخام: $...$ أو $$...$$ أو (...) أو [...].
  - ممنوع إظهار أوامر LaTeX مثل frac أو lim أو boxed أو begin.
  - اكتب الرياضيات بصيغة نصية/Unicode واضحة ومريحة للهاتف.
  - استخدم الرموز الرياضية مثل: → ، √ ، ∞ ، ≤ ، ≥ ، π ، ∫ عند الحاجة.
  - اكتب كل معادلة في سطر مستقل.
  - لا تكرر عبارات مثل "بالتعويض في البسط" و"بالتعويض في المقام" بلا حاجة.
  - اجعل الحل مختصرًا ومنظمًا، والنتيجة النهائية في سطر مستقل.

"""

        final_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": final_prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192
            }
        }

        final_response = requests.post(
            url,
            json=final_payload,
            timeout=180
        )

        final_response.raise_for_status()

        final_data = final_response.json()

        final_candidates = final_data.get(
            "candidates",
            []
        )

        if not final_candidates:
            return extracted_text

        final_parts = final_candidates[0].get(
            "content",
            {}
        ).get(
            "parts",
            []
        )

        final_text = "".join(
            part.get("text", "")
            for part in final_parts
            if "text" in part
        ).strip()

        return (
            final_text
            or extracted_text
            or "❌ لم يتم استخراج إجابة من الصورة."
        )

    except requests.RequestException as e:
        return (
            "❌ خطأ في الاتصال بـ Gemini: "
            f"{e}"
        )

    except Exception as e:
        print("IMAGE ANALYSIS ERROR:", repr(e))
        return (
            "❌ حدث خطأ أثناء تحليل الصورة: "
            f"{e}"
        )

