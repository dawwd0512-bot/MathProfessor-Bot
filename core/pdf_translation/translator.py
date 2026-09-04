import asyncio
import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.ai.gemini import ask_gemini


BASE_DIR = Path.home() / "MathProfessor-Bot"
DATA_DIR = BASE_DIR / "data"
TRANSLATED_DIR = DATA_DIR / "translated_pdfs"

MAX_CHARS_PER_CHUNK = 5000


# ============================================================
# FONT
# ============================================================

def find_arabic_font():
    candidates = [
        Path("/system/fonts/NotoNaskhArabic-Regular.ttf"),
        Path("/system/fonts/NotoSansArabic-Regular.ttf"),
        Path("/data/data/com.termux/files/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        BASE_DIR / "fonts" / "NotoNaskhArabic-Regular.ttf",
        BASE_DIR / "fonts" / "NotoSansArabic-Regular.ttf",
    ]

    for font_path in candidates:
        if font_path.exists():
            return font_path

    return None


ARABIC_FONT = find_arabic_font()

if ARABIC_FONT:
    try:
        pdfmetrics.registerFont(
            TTFont(
                "ArabicFont",
                str(ARABIC_FONT)
            )
        )
    except Exception:
        ARABIC_FONT = None


# ============================================================
# CLEANING
# ============================================================

def clean_translation(text: str) -> str:
    if not text:
        return ""

    text = text.replace("```", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")

    # لا نحذف $ لأن بعض المعادلات قد تحتاجه داخليًا.
    # لكننا نحاول إزالة Markdown غير الضروري.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# SPLIT TEXT
# ============================================================

def split_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK):
    """
    تقسيم النص إلى أجزاء صغيرة حتى لا نرسل PDF كامل
    إلى Gemini دفعة واحدة.
    """

    text = text.strip()

    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(current) + len(paragraph) + 2 <= max_chars:
            current += paragraph + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())

            # إذا كانت الفقرة نفسها ضخمة جدًا
            if len(paragraph) > max_chars:
                for i in range(0, len(paragraph), max_chars):
                    chunks.append(
                        paragraph[i:i + max_chars]
                    )

                current = ""
            else:
                current = paragraph + "\n\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ============================================================
# TRANSLATE
# ============================================================

def translate_text(text: str) -> str:
    if not text or not text.strip():
        return ""

    prompt = f"""
أنت مترجم أكاديمي متخصص في الرياضيات والعلوم.

ترجم النص الإنجليزي التالي إلى العربية ترجمة دقيقة جدًا.

القواعد:

1. لا تحذف أي معلومة.
2. لا تختصر.
3. لا تضف معلومات من عندك.
4. حافظ على ترتيب الفقرات والجمل.
5. حافظ على جميع الأرقام.
6. حافظ على أسماء المتغيرات مثل x و y و z.
7. حافظ على الرموز الرياضية.
8. حافظ على المعادلات قدر الإمكان.
9. لا تحول المعادلة إلى شرح نصي.
10. لا تغير وحدات القياس.
11. ترجم المصطلحات العلمية والرياضية ترجمة أكاديمية صحيحة.
12. عند الحاجة، يمكن وضع المصطلح الإنجليزي بين قوسين بعد ترجمته.
13. لا تضف عنوانًا غير موجود في النص.
14. لا تضف مقدمة أو خاتمة.
15. أعد الترجمة فقط.
16. لا تستخدم Markdown للعناوين.
17. لا تستخدم ```.
18. لا تضف تعليقات على الترجمة.
19. إذا كان هناك جزء غير واضح، لا تخترع معلومة.
20. حافظ على ترتيب المعادلات والأمثلة.

النص:

{text}
"""

    result = ask_gemini(
        prompt,
        [],
        []
    )

    return clean_translation(result)


async def translate_text_async(text: str) -> str:
    return await asyncio.to_thread(
        translate_text,
        text
    )


# ============================================================
# EXTRACT PDF TEXT
# ============================================================

def extract_pdf_text(input_pdf: str) -> str:
    reader = PdfReader(input_pdf)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            print(
                f"⚠️ تعذر قراءة الصفحة {page_number}: {e}"
            )
            text = ""

        if text.strip():
            pages.append(
                f"[صفحة {page_number}]\n{text.strip()}"
            )

    return "\n\n".join(pages)


# ============================================================
# PDF TEXT WRAPPING
# ============================================================

def prepare_pdf_lines(text: str, max_chars=75):
    """
    تحويل النص إلى أسطر مناسبة للـ PDF.
    """

    lines = []

    for paragraph in text.splitlines():
        paragraph = paragraph.strip()

        if not paragraph:
            lines.append("")
            continue

        # النص العربي يحتاج معالجة خاصة في العرض.
        # في المرحلة الأولى نحافظ على النص كما هو.
        while len(paragraph) > max_chars:
            cut = paragraph.rfind(" ", 0, max_chars)

            if cut <= 0:
                cut = max_chars

            lines.append(
                paragraph[:cut].strip()
            )

            paragraph = paragraph[cut:].strip()

        if paragraph:
            lines.append(paragraph)

    return lines


# ============================================================
# CREATE PDF
# ============================================================

def create_translated_pdf(
    translated_text: str,
    output_path: Path
):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    page_width, page_height = A4

    pdf = canvas.Canvas(
        str(output_path),
        pagesize=A4
    )

    if ARABIC_FONT:
        pdf.setFont(
            "ArabicFont",
            12
        )
    else:
        pdf.setFont(
            "Helvetica",
            11
        )

    margin = 45

    y = page_height - margin

    line_height = 18

    lines = prepare_pdf_lines(
        translated_text
    )

    for line in lines:

        if y < margin:
            pdf.showPage()

            if ARABIC_FONT:
                pdf.setFont(
                    "ArabicFont",
                    12
                )
            else:
                pdf.setFont(
                    "Helvetica",
                    11
                )

            y = page_height - margin

        if not line:
            y -= line_height
            continue

        # reportlab لا يقوم بترتيب العربية RTL بشكل كامل
        # بدون reshaping/bidi.
        # لذلك نضع النص كما خرج من النموذج في هذه المرحلة.
        pdf.drawString(
            margin,
            y,
            line
        )

        y -= line_height

    pdf.save()


# ============================================================
# MAIN PDF TRANSLATOR
# ============================================================

def translate_pdf(input_pdf: str) -> str:

    input_path = Path(input_pdf)

    if not input_path.exists():
        raise FileNotFoundError(
            f"PDF غير موجود:\n{input_path}"
        )

    if input_path.suffix.lower() != ".pdf":
        raise ValueError(
            "الملف يجب أن يكون PDF."
        )

    TRANSLATED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        TRANSLATED_DIR
        / f"{input_path.stem}_AR.pdf"
    )

    print(
        f"📄 قراءة PDF: {input_path}"
    )

    original_text = extract_pdf_text(
        str(input_path)
    )

    if not original_text.strip():
        raise RuntimeError(
            "لم يتم استخراج أي نص من ملف PDF."
        )

    print(
        f"📝 حجم النص المستخرج: {len(original_text)} حرف"
    )

    chunks = split_text(
        original_text
    )

    print(
        f"📚 عدد أجزاء الترجمة: {len(chunks)}"
    )

    translated_chunks = []

    for index, chunk in enumerate(
        chunks,
        start=1
    ):
        print(
            f"🌍 ترجمة الجزء {index}/{len(chunks)}..."
        )

        translated = translate_text(
            chunk
        )

        if translated:
            translated_chunks.append(
                translated
            )

    if not translated_chunks:
        raise RuntimeError(
            "لم يتم الحصول على ترجمة من Gemini."
        )

    translated_text = "\n\n".join(
        translated_chunks
    )

    print(
        "📄 إنشاء PDF العربي..."
    )

    create_translated_pdf(
        translated_text,
        output_path
    )

    print(
        f"✅ تم إنشاء الملف:\n{output_path}"
    )

    return str(output_path)
