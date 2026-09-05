from pathlib import Path

from core.files.image import read_image
from core.files.video import extract_video_frames
from core.files.video_transcript import transcribe_with_timestamps
from core.files.video_timeline import build_video_timeline


def build_video_evidence(
    video_path,
    wav_path,
    output_dir,
    max_frames=None,
):
    """
    يبني Evidence موحد للفيديو:

    Video
      ├── Whisper transcript
      ├── sampled frames
      ├── OCR
      └── timestamped timeline
    """

    video_path = str(video_path)
    wav_path = str(wav_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Transcript
    transcript = transcribe_with_timestamps(wav_path)

    # 2. Frames
    frames_dir = output_dir / "frames"

    frames = extract_video_frames(
        video_path,
        frames_dir,
        max_frames=max_frames,
    )

    # 3. OCR
    visual_evidence = []

    for frame in frames:
        frame_path = frame["path"]

        try:
            screen_text = read_image(frame_path) or ""
        except Exception as e:
            print("VIDEO EVIDENCE OCR ERROR:", e)
            screen_text = ""

        visual_evidence.append({
            "timestamp": float(frame["timestamp"]),
            "frame_path": frame_path,
            "screen_text": screen_text,
        })

    # 4. Timeline
    timeline = build_video_timeline(
        transcript,
        visual_evidence,
    )

    return {
        "video_path": video_path,
        "transcript": transcript,
        "visual_evidence": visual_evidence,
        "timeline": timeline,
    }
