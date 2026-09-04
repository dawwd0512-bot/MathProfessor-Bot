from .phone import open_url, open_app

APPS = {
    "يوتيوب": "com.google.android.youtube",
}

def execute(command):
    text = command.strip()

    if text in APPS:
        if open_app(APPS[text]):
            return f"تم فتح {text} ✅"
        return f"تعذر فتح {text} ❌"

    if text.startswith(("افتح ", "open ")):
        target = text.split(maxsplit=1)[1]

        if target in APPS:
            if open_app(APPS[target]):
                return f"تم فتح {target} ✅"
            return f"تعذر فتح {target} ❌"

        if target.startswith(("http://", "https://")):
            open_url(target)
            return "تم فتح الرابط ✅"

    return "الأمر غير مدعوم حاليًا."
