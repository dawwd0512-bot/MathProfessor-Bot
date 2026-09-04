from pathlib import Path
import subprocess
import uuid

BASE_DIR = Path.home() / "MathProfessor-Bot"
VIDEO_DIR = BASE_DIR / "data" / "videos"


def run_ffmpeg(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed:\n" + result.stderr[-5000:]
        )


def get_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return float(result.stdout.strip())


def escape_text(text):
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


def build_motion_filter(camera, duration):
    """
    حركات كاميرا بسيطة باستخدام FFmpeg.
    """

    frames = max(int(float(duration) * 30), 1)

    if camera == "slow_zoom_in":
        return (
            f"zoompan="
            f"z='min(zoom+0.0015,1.18)':"
            f"d={frames}:"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"s=1280x720:"
            f"fps=30"
        )

    if camera == "push_in":
        return (
            f"zoompan="
            f"z='min(zoom+0.002,1.25)':"
            f"d={frames}:"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"s=1280x720:"
            f"fps=30"
        )

    if camera == "pull_back":
        return (
            f"zoompan="
            f"z='max(1.25-0.002*on,1.0)':"
            f"d=1:"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"s=1280x720:"
            f"fps=30"
        )

    if camera == "macro_push":
        return (
            f"zoompan="
            f"z='min(zoom+0.003,1.35)':"
            f"d={frames}:"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"s=1280x720:"
            f"fps=30"
        )

    # orbit فعلياً سنطوره لاحقاً عندما ندخل صور/فيديوهات حقيقية.
    # حالياً نعطيه حركة خفيفة حتى لا يتعطل النظام.
    if camera == "orbit":
        return (
            f"zoompan="
            f"z='1.08':"
            f"d={frames}:"
            f"x='iw/2-(iw/zoom/2)+20*sin(on/18)':"
            f"y='ih/2-(ih/zoom/2)+10*cos(on/18)':"
            f"s=1280x720:"
            f"fps=30"
        )

    return None


def create_scene(
    scene_number,
    title,
    description,
    duration,
    camera="static",
    effects=None,
    text="",
):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    effects = effects or []

    output = (
        VIDEO_DIR
        / f"scene_{scene_number}_{uuid.uuid4().hex[:8]}.mp4"
    )

    safe_text = escape_text(
        text or description
    )

    filters = []

    motion_filter = build_motion_filter(
        camera,
        duration
    )

    if motion_filter:
        filters.append(motion_filter)

    # Slow motion
    if "slow_motion" in effects:
        filters.append(
            "setpts=1.5*PTS"
        )

    # إحساس حركة خفيف
    if "motion_blur" in effects:
        filters.append(
            "tblend=all_mode=average:all_opacity=0.35"
        )

    # Vignette سينمائية
    if "vignette" in effects:
        filters.append(
            "vignette=PI/5"
        )

    # Film grain بسيط
    if "film_grain" in effects:
        filters.append(
            "noise=alls=8:allf=t+u"
        )

    # النص
    filters.append(
        "drawtext="
        "fontcolor=white:"
        "fontsize=42:"
        "borderw=2:"
        "bordercolor=black:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2:"
        f"text='{safe_text}'"
    )

    filter_complex = ",".join(filters)

    command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i",
        "color=c=black:s=1280x720:r=30",
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

    run_ffmpeg(command)

    return str(output)


def combine_scenes(scene_files, output):
    concat_file = VIDEO_DIR / f"concat_{uuid.uuid4().hex}.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for scene in scene_files:
            f.write(
                f"file '{Path(scene).resolve()}'\n"
            )

    run_ffmpeg([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output),
    ])

    concat_file.unlink(missing_ok=True)

    return str(output)


def add_narration(video_file, audio_file, output):
    run_ffmpeg([
        "ffmpeg",
        "-y",
        "-i", str(video_file),
        "-i", str(audio_file),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output),
    ])

    return str(output)


def create_video_from_scenes(scene_files, narration_file):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    combined = (
        VIDEO_DIR
        / f"combined_{uuid.uuid4().hex[:8]}.mp4"
    )

    final = (
        VIDEO_DIR
        / f"generated_{uuid.uuid4().hex[:8]}.mp4"
    )

    combine_scenes(
        scene_files,
        combined
    )

    add_narration(
        combined,
        narration_file,
        final
    )

    return str(final)


def create_test_video(text="MathProfessor-Bot"):
    return create_scene(
        1,
        "Test",
        text,
        5
    )
