import re


def parse_timestamp(value):
    """
    يحول:
    3:42      -> 222.0
    01:03:42  -> 3822.0
    42        -> 42.0
    3.5       -> 3.5
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    try:
        if re.fullmatch(r"\d+(\.\d+)?", value):
            return float(value)

        parts = value.split(":")

        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds

        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds

    except Exception:
        return None

    return None


def query_timeline_at(timeline, timestamp):
    """
    يرجع مقطع الـtimeline الموجود عند التوقيت المحدد.
    """

    target = parse_timestamp(timestamp)

    if target is None:
        return []

    matches = []

    for item in timeline:
        start = float(item["start"])
        end = float(item["end"])

        if start <= target < end:
            matches.append(item)

    return matches


def query_visuals_at(timeline, timestamp):
    """
    يرجع اللقطات الأقرب للتوقيت المطلوب
    من المقطع الزمني المطابق.
    """

    matches = query_timeline_at(
        timeline,
        timestamp,
    )

    visuals = []

    for item in matches:
        visuals.extend(item.get("visuals", []))

    return visuals


def format_query_result(timeline, timestamp):
    """
    يحول نتيجة سؤال زمني إلى Evidence نصي منظم.
    """

    matches = query_timeline_at(
        timeline,
        timestamp,
    )

    if not matches:
        return ""

    parts = []

    for item in matches:
        lines = [
            f"[{item['start']:.2f}s → {item['end']:.2f}s]",
            f"الكلام: {item['text']}",
        ]

        for visual in item.get("visuals", []):
            lines.append(
                f"لقطة عند {float(visual['timestamp']):.2f}s:"
            )

            screen_text = (
                visual.get("screen_text") or ""
            ).strip()

            if screen_text:
                lines.append(
                    f"النص الظاهر: {screen_text}"
                )

            frame_path = visual.get("frame_path")

            if frame_path:
                lines.append(
                    f"الصورة: {frame_path}"
                )

        parts.append("\n".join(lines))

    return "\n\n".join(parts)
