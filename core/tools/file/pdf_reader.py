from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
import tempfile
import os


def read_pdf(path):
    """
    يحاول أولاً استخراج النص مباشرة.
    إذا فشل، يستخدم OCR بالعربية.
    """

    # ===== الطريقة الأولى: pypdf =====
    try:
        reader = PdfReader(path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        if text.strip():
            return text

    except Exception:
        pass

    # ===== الطريقة الثانية: OCR =====
    try:

        images = convert_from_path(path, dpi=300)

        result = ""

        for img in images:

            with tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False
            ) as temp:

                img.save(temp.name)

                page_text = pytesseract.image_to_string(
                    temp.name,
                    lang="ara"
                )

                result += page_text + "\n"

                os.remove(temp.name)

        if result.strip():
            return result

        return "❌ لم يتم العثور على نص داخل الملف."

    except Exception as e:

        return f"❌ فشل OCR:\n{e}"
