import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path.home() / "MathProfessor-Bot"
IMAGE_DIR = BASE_DIR / "data" / "generated_images"

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found")


def generate_scene_image(prompt: str, filename: str) -> str:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    output = IMAGE_DIR / filename

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-3.1-flash-image:generateContent"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "16:9"
            }
        }
    }

    r = requests.post(
        url,
        params={"key": API_KEY},
        json=payload,
        timeout=120,
    )

    print("IMAGE API HTTP:", r.status_code)

    if not r.ok:
        raise RuntimeError(r.text)

    data = r.json()

    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData")

            if inline and inline.get("data"):
                image_data = base64.b64decode(inline["data"])
                output.write_bytes(image_data)
                return str(output)

    raise RuntimeError(
        "Gemini returned no image:\n" + str(data)[:5000]
    )
