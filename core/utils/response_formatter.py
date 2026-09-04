import re


def _normalize(text):
    text = str(text)

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # إزالة رموز Markdown غير المطلوبة
    text = text.replace("$", "")
    text = text.replace("```", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)

    # إزالة خطوط الفصل الزائدة
    text = re.sub(r"(?m)^\s*[-_=]{3,}\s*$", "", text)

    # تنظيف المسافات
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _remove_exact_duplicate(text):
    parts = [
        part.strip()
        for part in re.split(r"\n\s*\n", text)
        if part.strip()
    ]

    if not parts:
        return ""

    result = []
    seen = set()

    for part in parts:
        key = re.sub(r"\s+", " ", part).strip().lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(part)

    return "\n\n".join(result)


def _remove_repeated_sections(text):
    # يعالج حالة إعادة نفس مجموعة الأسئلة كاملة مرة ثانية
    lines = text.splitlines()

    cleaned = []
    previous_question = None
    skip = False

    for line in lines:
        stripped = line.strip()

        match = re.match(
            r"^(السؤال|سؤال)\s*(\d+)\s*:?\s*$",
            stripped,
            re.IGNORECASE,
        )

        if match:
            number = match.group(2)

            if number == previous_question:
                skip = True
                continue

            previous_question = number
            skip = False

        if not skip:
            cleaned.append(line)

    return "\n".join(cleaned)


def format_response(response):
    if response is None:
        return ""

    text = _normalize(response)

    if not text:
        return ""

    # أولاً إزالة الفقرات المتطابقة
    text = _remove_exact_duplicate(text)

    # ثم إزالة تكرار الأقسام المتتابعة
    text = _remove_repeated_sections(text)

    # تنظيف نهائي
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
