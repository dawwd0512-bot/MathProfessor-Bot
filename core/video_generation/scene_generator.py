from pathlib import Path
import subprocess


BASE_DIR = Path.home() / "MathProfessor-Bot"
VIDEO_DIR = BASE_DIR / "data" / "videos"


def create_scene(
    scene_number: int,
    title: str,
    description: str,
    duration: int = 5,
):
    VIDEO_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output = (
        VIDEO_DIR
        / f"scene_{scene_number}.mp4"
    )

    # خلفية متدرجة الحركة + عنوان المشهد.
    # هذا اختبار أولي قبل إدخال مولد صور/فيديو خارجي.
    filter_complex = (
        "drawbox="
        "x=0:y=0:w=iw:h=ih:"
        "color=black@0.15:"
        "t=fill,"
        "drawtext="
        "fontcolor=white:"
        "fontsize=52:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2-40:"
        f"text='{title}',"
        "drawtext="
        "fontcolor=white@0.75:"
        "fontsize=28:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2+40:"
        f"text='{description[:120]}'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i",
        "color=c=0x101522:s=1280x720:r=30",
        "-t",
        str(duration),
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr[-4000:]
        )

    return str(output)
