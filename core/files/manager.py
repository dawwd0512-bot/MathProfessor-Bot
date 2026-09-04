import os

from core.files.pdf import read_pdf
from core.files.docx import read_docx
from core.files.image import read_image
from core.files.video import read_video
from core.files.storage import save_file
from core.rag.rag_manager import RAGManager

rag = RAGManager()


def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return "pdf"

    if ext in [".docx", ".doc"]:
        return "docx"

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return "image"

    if ext in [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]:
        return "video"

    return "unknown"


def process_file(file_path, user_id):
    filename = os.path.basename(file_path)

    file_type = get_file_type(filename)

    if file_type == "pdf":
        content = read_pdf(file_path)

    elif file_type == "docx":
        content = read_docx(file_path)

    elif file_type == "image":
        content = read_image(file_path)

    elif file_type == "video":
        content = read_video(file_path)

    else:
        return {
            "status": "error",
            "message": "نوع الملف غير مدعوم"
        }

    if not content:
        return {
            "status": "error",
            "message": "لم يتم استخراج محتوى من الملف"
        }

    chunks = rag.load_document(
        user_id,
        content
    )

    print("=" * 60)
    print("RAG CHUNKS:", chunks)

    saved_path = save_file(
        user_id,
        filename,
        open(file_path, "rb").read()
    )

    return {
        "status": "success",
        "type": file_type,
        "path": saved_path,
        "content": content,
        "chunks": chunks,
    }
