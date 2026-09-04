import re
from .book_analyzer import Chapter


PATTERNS = [
    re.compile(r"^\s*P\.(\d+)\s+(.+?)\s*$", re.I),
    re.compile(r"^\s*Chapter\s*\(?(\d+)\)?\s*(.*)$", re.I),
]


def detect_chapters(text: str):
    lines = text.splitlines()

    sections = []
    current = None
    buffer = []

    def save_current():
        nonlocal current, buffer

        if current is not None:
            current.text = "\n".join(buffer).strip()

            if current.text:
                sections.append(current)

    for line in lines:
        clean = line.strip()

        if not clean:
            continue

        match = None

        for pattern in PATTERNS:
            found = pattern.match(clean)

            if found:
                match = found
                break

        if match:
            save_current()

            number = int(match.group(1))
            title = match.group(2).strip()

            if not title:
                title = f"Chapter {number}"

            current = Chapter(
                number=number,
                title=title,
            )

            buffer = []

        elif current is not None:
            buffer.append(clean)

    save_current()

    return sections
