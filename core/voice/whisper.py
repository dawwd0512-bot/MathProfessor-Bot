import os
import subprocess

BASE_DIR = os.path.expanduser("~/MathProfessor-Bot")

WHISPER_BIN = os.path.join(
    BASE_DIR,
    "third_party/whisper.cpp/build/bin/whisper-cli"
)

WHISPER_MODEL = os.path.join(
    BASE_DIR,
    "third_party/whisper.cpp/models/ggml-tiny-q5_1.bin"
)


def transcribe_audio(audio_path: str) -> str:
    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-l", "en",
        "-nt",
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    output = result.stdout + "\n" + result.stderr

    if result.returncode != 0:
        raise RuntimeError(output.strip())

    lines = []

    for line in output.splitlines():
        line = line.strip()

        if line.startswith("[") and "]" in line:
            text = line.split("]", 1)[1].strip()

            if text:
                lines.append(text)

    return " ".join(lines).strip()
