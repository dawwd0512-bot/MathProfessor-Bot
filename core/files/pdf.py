import os
import subprocess
import tempfile
from pathlib import Path

from pdf2image import convert_from_path


def _ocr_image(image_path):
    """Run Arabic + English OCR."""
    try:
        result = subprocess.run(
            [
                "tesseract",
                str(image_path),
                "stdout",
                "-l",
                "ara+eng",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        return result.stdout.strip()

    except Exception:
        return ""


def read_pdf(path):
    path = str(path)

    # ---------------------------------------------------------
    # 1. Try normal PDF text extraction
    # ---------------------------------------------------------
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)

        pages = []

        for i, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""

                if text.strip():
                    pages.append(f"[الصفحة {i}]\n{text}")
                else:
                    pages.append(f"[الصفحة {i}]")

            except Exception:
                pages.append(f"[الصفحة {i}]")

        text = "\n\n".join(pages)

        # If meaningful text exists, return it.
        if len(text.strip()) > 50:
            return text

    except Exception:
        pass

    # ---------------------------------------------------------
    # 2. OCR fallback
    # ---------------------------------------------------------
    ocr_pages = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        try:
            images = convert_from_path(
                path,
                dpi=300,
                fmt="png",
                output_folder=str(tmp),
                thread_count=1,
            )

            for i, image in enumerate(images, 1):
                image_path = tmp / f"page-{i}.png"
                image.save(image_path)

                ocr_text = _ocr_image(image_path)

                if ocr_text:
                    ocr_pages.append(
                        f"[الصفحة {i}]\n{ocr_text}"
                    )

        except Exception:
            pass

    return "\n\n".join(ocr_pages)
