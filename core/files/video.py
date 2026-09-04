import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _video_duration(file_path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        return float(result.stdout.strip())

    except Exception as e:
        print("VIDEO PROBE ERROR:", e)
        return 0.0


def _ocr_frame(image_path):
    try:
        from core.files.image import read_image
        return read_image(str(image_path))
    except Exception as e:
        print("VIDEO OCR ERROR:", e)
        return ""


def read_video(file_path):
    if not os.path.isfile(file_path):
        return ""

    if shutil.which("ffmpeg") is None:
        print("VIDEO ERROR: ffmpeg not installed")
        return ""

    duration = _video_duration(file_path)

    if duration <= 0:
        return ""

    if duration <= 30:
        frame_count = 5
    elif duration <= 120:
        frame_count = 8
    elif duration <= 600:
        frame_count = 12
    else:
        frame_count = 15

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        output_pattern = tmp / "frame-%03d.jpg"

        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", file_path,
                    "-vf",
                    f"fps={frame_count}/{max(duration, 1):.3f},"
                    "scale='min(1600,iw)':-2",
                    "-q:v", "2",
                    str(output_pattern),
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print("VIDEO FRAME ERROR:", result.stderr)
                return ""

        except Exception as e:
            print("VIDEO FFMPEG ERROR:", e)
            return ""

        texts = []

        for frame in sorted(tmp.glob("frame-*.jpg")):
            text = _ocr_frame(frame)

            if text and len(text.strip()) >= 3:
                texts.append(text.strip())

        if not texts:
            return ""

        unique = []
        seen = set()

        for text in texts:
            key = " ".join(text.split())

            if key not in seen:
                seen.add(key)
                unique.append(text)

        return "\n\n".join(
            f"[لقطة الفيديو {i}]\n{text}"
            for i, text in enumerate(unique, 1)
        )
