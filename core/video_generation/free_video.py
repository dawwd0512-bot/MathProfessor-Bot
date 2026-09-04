from pathlib import Path
import subprocess
import uuid

BASE = Path.home() / "MathProfessor-Bot"
OUT = BASE / "data" / "videos"
OUT.mkdir(parents=True, exist_ok=True)


def run(cmd):
    r = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])


def make_video(title, subtitle, seconds=10):
    output = OUT / f"free_{uuid.uuid4().hex[:8]}.mp4"

    vf = (
        "drawbox=x=0:y=0:w=iw:h=ih:"
        "color=0x101522:t=fill,"
        "drawgrid=width=80:height=80:"
        "thickness=1:color=0x26344a@0.35,"
        "drawtext="
        "text='MathProfessor-Bot':"
        "fontcolor=0x7dd3fc:"
        "fontsize=30:"
        "x=50:y=45,"
        "drawtext="
        f"text='{title}':"
        "fontcolor=white:"
        "fontsize=64:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2-45,"
        "drawtext="
        f"text='{subtitle}':"
        "fontcolor=0xcccccc:"
        "fontsize=32:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2+55,"
        "fade=t=in:st=0:d=1,"
        f"fade=t=out:st={max(seconds-1,1)}:d=1"
    )

    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x101522:s=1280x720:r=30",
        "-t", str(seconds),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ])

    return output


if __name__ == "__main__":
    video = make_video(
        "التكامل المحدد",
        "Calculus 1 • المساحة تحت المنحنى",
        10,
    )
    print("VIDEO:", video)
