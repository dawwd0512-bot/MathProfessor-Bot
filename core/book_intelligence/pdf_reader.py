from pathlib import Path
from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))
    pages = []

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n--- PAGE {i} ---\n{text}")

    return "\n".join(pages)


def get_pdf_info(pdf_path: str) -> dict:
    path = Path(pdf_path)
    reader = PdfReader(str(path))

    return {
        "path": str(path),
        "pages": len(reader.pages),
        "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
    }
