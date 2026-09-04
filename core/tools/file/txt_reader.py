from pathlib import Path


def read_txt(path):

    try:

        return Path(path).read_text(
            encoding="utf-8",
            errors="ignore"
        )

    except Exception as e:

        return f"❌ خطأ في قراءة TXT:\n{e}"
