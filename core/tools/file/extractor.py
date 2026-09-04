from pathlib import Path

from core.tools.file.pdf_reader import read_pdf
from core.tools.file.docx_reader import read_docx
from core.tools.file.txt_reader import read_txt
from core.tools.file.image_reader import read_image


def extract(path):

    ext = Path(path).suffix.lower()


    if ext == ".pdf":
        return read_pdf(path)


    if ext == ".docx":
        return read_docx(path)


    if ext == ".txt":
        return read_txt(path)


    if ext in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:
        return read_image(path)


    return "❌ نوع الملف غير مدعوم."
