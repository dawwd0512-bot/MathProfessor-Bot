import os


def read_image(file_path):
    """
    OCR for JPG/JPEG/PNG/WEBP images and screenshots.
    Uses Pillow + Tesseract with Arabic and English.
    """

    try:
        from PIL import Image, ImageOps, ImageFilter
        import pytesseract

        if not os.path.isfile(file_path):
            return ""

        image = Image.open(file_path)

        # Normalize image
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")

        # Improve small screenshots / phone images
        width, height = image.size

        if max(width, height) < 1600:
            scale = 1600 / max(width, height)
            image = image.resize(
                (int(width * scale), int(height * scale)),
                Image.Resampling.LANCZOS,
            )

        # Grayscale
        gray = ImageOps.grayscale(image)

        # Light contrast enhancement
        gray = ImageOps.autocontrast(gray)

        results = []

        # Try normal OCR
        for psm in (6, 11):
            try:
                text = pytesseract.image_to_string(
                    gray,
                    lang="ara+eng",
                    config=f"--psm {psm}",
                ).strip()

                if text:
                    results.append(text)
            except Exception:
                pass

        if not results:
            return ""

        # Prefer the longest useful OCR result
        return max(results, key=len)

    except Exception as e:
        print("IMAGE OCR ERROR:", e)
        return ""
