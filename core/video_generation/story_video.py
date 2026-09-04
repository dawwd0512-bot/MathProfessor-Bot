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
        raise RuntimeError(r.stderr[-4000:])


def esc(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


def scene(number, title, description, duration=5):
    output = OUT / f"story_{number}_{uuid.uuid4().hex[:6]}.mp4"

    title = esc(title)
    description = esc(description)

    # خلفية متحركة بسيطة
    vf = (
        "drawbox=x=0:y=0:w=iw:h=ih:"
        "color=0x0b1020:t=fill,"
        "drawgrid=width=100:height=100:"
        "thickness=1:color=0x24324a@0.25,"
        "drawtext="
        "text='MATH PROFESSOR':"
        "fontcolor=0x7dd3fc:"
        "fontsize=26:"
        "x=50:y=40,"
        "drawtext="
        f"text='{title}':"
        "fontcolor=white:"
        "fontsize=58:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2-70,"
        "drawtext="
        f"text='{description}':"
        "fontcolor=0xdddddd:"
        "fontsize=30:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2+20,"
        "fade=t=in:st=0:d=0.8,"
        f"fade=t=out:st={duration-0.8}:d=0.8"
    )

    run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "color=c=0x0b1020:s=1280x720:r=30",
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output),
    ])

    return output


def make_story():
    shots = [
        (
            "المشهد الأول",
            "الطالب يدخل القاعة",
            "الساعة تقترب من موعد امتحان Calculus"
        ),
        (
            "المشهد الثاني",
            "السؤال الصعب",
            "يظهر سؤال عن المساحة تحت المنحنى"
        ),
        (
            "المشهد الثالث",
            "لحظة الفهم",
            "تظهر فكرة التكامل وتتحول المنطقة إلى مساحة"
        ),
        (
            "المشهد الرابع",
            "الحل",
            "يكتب الطالب حدود التكامل ويبدأ الحساب"
        ),
        (
            "المشهد الخامس",
            "النهاية",
            "الطالب يبتسم بعد أن وجد الإجابة"
        ),
    ]

    files = []

    for i, (title, main, desc) in enumerate(shots, 1):
        print(f"🎬 Scene {i}/5: {main}")
        files.append(
            scene(
                i,
                title,
                f"{main} — {desc}",
                4,
            )
        )

    concat = OUT / f"story_{uuid.uuid4().hex[:8]}.txt"
    final = OUT / f"story_final_{uuid.uuid4().hex[:8]}.mp4"

    with open(concat, "w") as f:
        for file in files:
            f.write(f"file '{file.resolve()}'\n")

    run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(final),
    ])

    concat.unlink(missing_ok=True)

    print("✅ STORY VIDEO:", final)
    return final


if __name__ == "__main__":
    make_story()
