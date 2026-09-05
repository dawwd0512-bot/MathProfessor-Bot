from pathlib import Path


def _overlap(start_a, end_a, start_b, end_b):
    return max(start_a, start_b) < min(end_a, end_b)


def build_video_timeline(transcript_segments, visual_evidence):
    """
    يربط الكلام المسجل بالفريمات القريبة منه زمنيًا.

    transcript_segments:
    [
        {
            "start": 0.0,
            "end": 3.0,
            "text": "..."
        }
    ]

    visual_evidence:
    [
        {
            "timestamp": 2.0,
            "frame_path": "...",
            "screen_text": "..."
        }
    ]
    """

    timeline = []

    for segment in transcript_segments:
        start = float(segment["start"])
        end = float(segment["end"])

        visuals = []

        for evidence in visual_evidence:
            timestamp = float(evidence["timestamp"])

            # نعتبر الفريم مرتبطًا بالمقطع إذا كان داخل المقطع.
            if start <= timestamp < end:
                visuals.append(evidence)

        # إذا لم يوجد فريم داخل المقطع، نأخذ أقرب فريم.
        if not visuals and visual_evidence:
            nearest = min(
                visual_evidence,
                key=lambda item: abs(
                    float(item["timestamp"]) - start
                ),
            )
            visuals.append(nearest)

        timeline.append(
            {
                "start": start,
                "end": end,
                "text": segment["text"],
                "visuals": visuals,
            }
        )

    return timeline


def format_video_timeline(timeline):
    """
    يحول الـ timeline إلى نص منظم قابل للإرسال لاحقًا إلى LLM.
    """

    parts = []

    for item in timeline:
        start = item["start"]
        end = item["end"]

        lines = [
            f"[{start:.2f}s → {end:.2f}s]",
            f"الكلام: {item['text']}",
        ]

        for visual in item.get("visuals", []):
            timestamp = float(visual["timestamp"])
            screen_text = (
                visual.get("screen_text") or ""
            ).strip()

            lines.append(
                f"لقطة عند {timestamp:.2f}s:"
            )

            if screen_text:
                lines.append(
                    f"النص الظاهر: {screen_text}"
                )
            else:
                lines.append(
                    "النص الظاهر: لا يوجد نص مقروء"
                )

            frame_path = visual.get("frame_path")
            if frame_path:
                lines.append(
                    f"الصورة: {frame_path}"
                )

        parts.append("\n".join(lines))

    return "\n\n".join(parts)
