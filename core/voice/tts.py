import edge_tts
from pathlib import Path
import re


ARABIC_VOICE = "ar-SA-HamedNeural"
ENGLISH_VOICE = "en-US-GuyNeural"


def detect_language(text: str) -> str:
    """
    Detect Arabic vs English based on the characters in the text.
    """
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    english_chars = len(re.findall(r"[A-Za-z]", text))

    if arabic_chars > english_chars:
        return "ar"

    return "en"


def get_voice(text: str) -> str:
    language = detect_language(text)

    if language == "ar":
        return ARABIC_VOICE

    return ENGLISH_VOICE


async def text_to_speech(text: str, output_path: str):
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    voice = get_voice(text)

    print(f"TTS language: {detect_language(text)}")
    print(f"TTS voice: {voice}")

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
    )

    await communicate.save(str(output_path))

    return str(output_path)
