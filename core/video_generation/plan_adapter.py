from core.video_generation.shot_plan import Shot, VideoSequence


def choose_camera(description, index, total):
    text = description.lower()

    # الاقتراب له أولوية على كون اللقطة واسعة
    # إذا كانت اللقطة واسعة لكنها تتحرك نحو الهدف،
    # فالـ zoom أهم من وصف "لقطة واسعة".
    approach_words = [
        "اقتراب",
        "الاقتراب",
        "تقريب",
        "زووم",
        "zoom",
        "المركز",
        "نحو",
    ]

    if any(x in text for x in approach_words):
        return "slow_zoom_in"

    if any(x in text for x in [
        "لقطة نهائية",
        "خروج بطيء",
        "ابتعاد",
        "تراجع",
        "المشهد بالكامل",
    ]):
        return "pull_back"

    if "لقطة واسعة" in text:
        return "slow_zoom_in"

    if any(x in text for x in [
        "أفق الحدث",
        "تفصيل",
        "قريب",
        "سطح",
    ]):
        return "macro_push"

    if any(x in text for x in [
        "يدور",
        "دوران",
        "مادة تسقط",
        "يطير",
        "مركبة",
        "حركة",
    ]):
        return "orbit"

    if any(x in text for x in [
        "أستاذ",
        "يشرح",
        "يتحدث",
        "شخص",
        "رائد فضاء",
    ]):
        return "push_in"

    if index == 1:
        return "slow_zoom_in"

    if index == total:
        return "pull_back"

    return "orbit"


def choose_effects(description, camera):
    text = description.lower()
    effects = []

    if camera in ("orbit", "macro_push"):
        effects.append("motion_blur")

    if any(x in text for x in [
        "يدور",
        "تسقط",
        "انفجار",
        "يختفي",
        "يندفع",
        "يطير",
    ]):
        effects.append("slow_motion")

    if any(x in text for x in [
        "فضاء",
        "ليل",
        "مظلم",
        "كون",
        "ثقب أسود",
    ]):
        effects.append("vignette")

    if not effects:
        effects.append("film_grain")

    return effects


def choose_sfx(description):
    text = description.lower()

    if any(x in text for x in [
        "مقص",
        "معدني",
        "حديد",
        "إغلاق",
    ]):
        return "metal_click"

    if any(x in text for x in [
        "يطير",
        "يدور",
        "يندفع",
        "حركة",
    ]):
        return "whoosh"

    if any(x in text for x in [
        "انفجار",
        "انهيار",
    ]):
        return "impact"

    return ""


def plan_text_to_sequence(plan_text):
    lines = [
        line.strip()
        for line in plan_text.splitlines()
        if line.strip()
    ]

    title = "AI Cinematic Video"

    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "", 1).strip()
            break

    descriptions = []

    for line in lines:
        if not line[0].isdigit():
            continue

        if "." not in line:
            continue

        description = line.split(".", 1)[1].strip()

        if description:
            descriptions.append(description)

    if not descriptions:
        descriptions = [plan_text[:300]]

    shots = []

    total = len(descriptions)

    for index, description in enumerate(descriptions, 1):
        camera = choose_camera(
            description,
            index,
            total
        )

        effects = choose_effects(
            description,
            camera
        )

        sfx = choose_sfx(description)

        duration = 5

        if index == 1:
            transition_in = "fade"

        else:
            transition_in = "cut"

        if index == total:
            transition_out = "fade"

        else:
            transition_out = "cut"

        shots.append(
            Shot(
                duration=duration,
                visual=description,
                camera=camera,
                transition_in=transition_in,
                transition_out=transition_out,
                effects=effects,
                sound_effect=sfx,
            )
        )

    return VideoSequence(
        title=title,
        shots=shots,
    )
