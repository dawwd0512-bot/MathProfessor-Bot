import re
import asyncio
from pathlib import Path

import fitz
from pathlib import Path


from core.ai.gemini import ask_gemini


BATCH_SIZE = 4

ARABIC_FONT = "/system/fonts/NotoNaskhArabic-Regular.ttf"


# ============================================================
# ARABIC
# ============================================================

def prepare_arabic(text):
    """
    تجهيز النص العربي للـ PDF.
    PyMuPDF يتعامل مع RTL عند استخدام الخط العربي المناسب،
    لذلك لا نعتمد على python-bidi أو arabic-reshaper.
    """
    if not text:
        return ""

    return text


# ============================================================
# PROTECT MATHEMATICAL CONTENT
# ============================================================

def protect_special_content(text):

    protected = {}
    counter = 0

    patterns = [
        r'\$\$.*?\$\$',
        r'\$.*?\$',
        r'\\[A-Za-z]+',
        r'\b[A-Za-z]+\^\{[^}]+\}',
        r'\b[A-Za-z]+_\{[^}]+\}',
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            flags=re.DOTALL
        )

        for match in matches:

            if not match:
                continue

            if match in protected.values():
                continue

            token = f"MATHTOKEN{counter}ENDTOKEN"

            protected[token] = match

            text = text.replace(
                match,
                token
            )

            counter += 1

    return text, protected


def restore_special_content(
    text,
    protected
):

    for token, value in protected.items():
        text = text.replace(
            token,
            value
        )

    return text


# ============================================================
# CLEAN TRANSLATION
# ============================================================

def clean_translation(text):

    if not text:
        return ""

    # ممنوع الرموز غير المطلوبة
    text = text.replace("#", "")
    text = text.replace("$", "")

    # إزالة Markdown الشائع
    text = text.replace("```", "")
    text = text.replace("**", "")
    
    return text.strip()


# ============================================================
# TRANSLATION
# ============================================================

async def translate_text(text):

    if not text.strip():
        return ""

    safe_text, protected = (
        protect_special_content(text)
    )

    prompt = f"""
أنت مترجم أكاديمي محترف ومتخصص في ترجمة الكتب والمحاضرات
والمواد الرياضية والعلمية من الإنجليزية إلى العربية.

مهمتك ترجمة النص التالي ترجمة كاملة ودقيقة.

قواعد صارمة جداً:

1. ترجم كل النص بالكامل.
2. لا تلخص.
3. لا تحذف أي جملة.
4. لا تضف أي معلومة من عندك.
5. لا تشرح النص.
6. لا تعيد صياغة المحتوى إلا بالقدر الضروري للترجمة العربية الصحيحة.
7. حافظ على ترتيب الفقرات والجمل.
8. حافظ على الأرقام كما هي.
9. حافظ على أسماء المتغيرات كما هي.
10. حافظ على الوحدات كما هي.
11. حافظ على المعادلات الرياضية كما هي.
12. حافظ على الرموز الرياضية كما هي.
13. لا تغير أي شيء موجود داخل MATHTOKEN...ENDTOKEN.
14. لا تضف أي رمز #.
15. لا تضف أي رمز $.
16. لا تستخدم Markdown.
17. لا تستخدم النجوم للتنسيق.
18. لا تستخدم علامات # للعناوين.
19. لا تضف عناوين غير موجودة.
20. لا تضف ملاحظات أو تعليقات.
21. أخرج الترجمة فقط.
22. المصطلحات الرياضية يجب أن تترجم ترجمة أكاديمية صحيحة.
23. إذا كان المصطلح له ترجمة رياضية عربية معروفة فاستخدمها.
24. إذا كان هناك رمز أو متغير أو تعبير رياضي، لا تعبث به.

النص الأصلي:

{safe_text}
"""

    result = await asyncio.to_thread(
        ask_gemini,
        prompt,
        [],
        []
    )

    if not result:
        raise RuntimeError(
            "لم يتم الحصول على ترجمة."
        )

    result = restore_special_content(
        result,
        protected
    )

    result = clean_translation(
        result
    )

    return result


# ============================================================
# PDF PAGE
# ============================================================

def extract_page_text(page):

    return page.get_text(
        "text"
    ).strip()


# ============================================================
# ADD TEXT TO PDF
# ============================================================

def add_english_and_arabic(
    output_page,
    english,
    arabic
):

    width = output_page.rect.width
    height = output_page.rect.height

    margin = 35

    # --------------------------------------------------------
    # English
    # --------------------------------------------------------

    english_box = fitz.Rect(
        margin,
        margin,
        width - margin,
        height * 0.46
    )

    output_page.insert_textbox(
        english_box,
        english,
        fontsize=8,
        fontname="helv",
        align=0,
        lineheight=1.15
    )

    # --------------------------------------------------------
    # Separator
    # --------------------------------------------------------

    separator_y = height * 0.475

    output_page.draw_line(
        fitz.Point(
            margin,
            separator_y
        ),
        fitz.Point(
            width - margin,
            separator_y
        ),
        width=0.5
    )

    # --------------------------------------------------------
    # Arabic
    # --------------------------------------------------------

    arabic = prepare_arabic(
        arabic
    )

    arabic_box = fitz.Rect(
        margin,
        height * 0.50,
        width - margin,
        height - margin
    )

    output_page.insert_textbox(
        arabic_box,
        arabic,
        fontsize=8,
        fontfile=ARABIC_FONT,
        align=2,
        lineheight=1.2
    )


# ============================================================
# TRANSLATE PDF
# ============================================================

async def translate_pdf(
    input_pdf,
    output_pdf,
    progress_callback=None
):

    input_pdf = Path(
        input_pdf
    )

    output_pdf = Path(
        output_pdf
    )

    if not input_pdf.exists():
        raise FileNotFoundError(
            f"الملف غير موجود:\n{input_pdf}"
        )

    output_pdf.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    source = fitz.open(
        str(input_pdf)
    )

    output = fitz.open()

    total_pages = len(source)

    print(
        f"📚 عدد الصفحات: {total_pages}"
    )

    try:

        for page_index in range(
            total_pages
        ):

            page = source[
                page_index
            ]

            print(
                f"📄 ترجمة الصفحة "
                f"{page_index + 1}/{total_pages}"
            )

            english_text = (
                extract_page_text(
                    page
                )
            )

            if not english_text:

                new_page = output.new_page(
                    width=page.rect.width,
                    height=page.rect.height
                )

                continue

            arabic_text = (
                await translate_text(
                    english_text
                )
            )

            new_page = output.new_page(
                width=page.rect.width,
                height=page.rect.height
            )

            add_english_and_arabic(
                new_page,
                english_text,
                arabic_text
            )

            if progress_callback:

                await progress_callback(
                    page_index + 1,
                    total_pages
                )

    finally:

        source.close()

    print(
        "💾 جاري حفظ PDF..."
    )

    output.save(
        str(output_pdf),
        garbage=4,
        deflate=True,
        clean=True
    )

    output.close()

    print(
        f"✅ تم إنشاء الملف:\n"
        f"{output_pdf}"
    )

    return str(
        output_pdf
    )
