import os
import base64
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY غير موجود")

IMAGE_DIR = Path.home() / "MathProfessor-Bot" / "data" / "generated_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

URL = (
    "https://generativelanguage.googleapis.com/v1/"
    "models/gemini-3.1-flash-image:generateContent"
)


def generate_image(prompt: str, filename: str = "generated.png") -> str:
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"]
        }
    }

    request = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Gemini HTTP {e.code}:\\n{body[:4000]}"
        ) from e

    candidates = data.get("candidates", [])

    if not candidates:
        raise RuntimeError(
            "Gemini لم يُرجع نتيجة:\n"
            + json.dumps(data, ensure_ascii=False)[:2000]
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")

        if inline and inline.get("data"):
            mime = inline.get("mimeType", "image/png")
            ext = ".jpg" if "jpeg" in mime else ".png"

            output = IMAGE_DIR / filename

            if output.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                output = output.with_suffix(ext)

            output.write_bytes(
                base64.b64decode(inline["data"])
            )

            return str(output)

    raise RuntimeError("Gemini لم يُرجع بيانات صورة.")


if __name__ == "__main__":
    path = generate_image(
        "A cute orange cat sitting on mathematics books, "
        "clean digital illustration.",
        "cat_test.png",
    )

    print("IMAGE:", path)
