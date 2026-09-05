import re
import subprocess
import tempfile
from pathlib import Path


def _find_whisper_paths():
    base_dir = Path(__file__).resolve().parents[2]

    whisper_bin = (
        base_dir
        / "third_party"
        / "whisper.cpp"
        / "build"
        / "bin"
        / "whisper-cli"
    )

    whisper_model = (
        base_dir
        / "third_party"
        / "whisper.cpp"
        / "models"
        / "ggml-tiny-q5_1.bin"
    )

    return whisper_bin, whisper_model


def _parse_srt_time(value):
    hours, minutes, seconds, milliseconds = map(
        int,
        re.split(r"[:,]", value.strip())
    )

    return (
        hours * 3600
        + minutes * 60
        + seconds
        + milliseconds / 1000
    )


def _parse_srt(srt_text):
    segments = []

    blocks = re.split(
        r"\n\s*\n",
        srt_text.strip(),
    )

    for block in blocks:
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if len(lines) < 3:
            continue

        timing = lines[1]

        if "-->" not in timing:
            continue

        start_text, end_text = [
            part.strip()
            for part in timing.split("-->", 1)
        ]

        try:
            start = _parse_srt_time(start_text)
            end = _parse_srt_time(end_text)
        except Exception:
            continue

        text = " ".join(lines[2:]).strip()

        if not text:
            continue

        segments.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
            }
        )

    return segments


def transcribe_with_timestamps(wav_file):
    """
    تفريغ صوت الفيديو مع التوقيتات.

    يعيد:
    [
        {
            "start": 0.0,
            "end": 3.0,
            "text": "..."
        }
    ]
    """

    wav_file = Path(wav_file)

    if not wav_file.is_file():
        raise FileNotFoundError(
            f"ملف الصوت غير موجود:\n{wav_file}"
        )

    whisper_bin, whisper_model = _find_whisper_paths()

    if not whisper_bin.is_file():
        raise FileNotFoundError(
            f"Whisper غير موجود:\n{whisper_bin}"
        )

    if not whisper_model.is_file():
        raise FileNotFoundError(
            f"موديل Whisper غير موجود:\n{whisper_model}"
        )

    with tempfile.TemporaryDirectory() as tmp:
        output_base = Path(tmp) / "transcript"

        command = [
            str(whisper_bin),
            "-m",
            str(whisper_model),
            "-f",
            str(wav_file),
            "-l",
            "auto",
            "-osrt",
            "-of",
            str(output_base),
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Whisper timestamp transcription failed:\n"
                + result.stderr[-3000:]
            )

        srt_file = Path(str(output_base) + ".srt")

        if not srt_file.is_file():
            raise RuntimeError(
                "Whisper لم ينشئ ملف SRT."
            )

        srt_text = srt_file.read_text(
            encoding="utf-8",
            errors="replace",
        )

    segments = _parse_srt(srt_text)

    if not segments:
        raise RuntimeError(
            "Whisper لم يُرجع مقاطع نصية بتوقيتات."
        )

    return segments
