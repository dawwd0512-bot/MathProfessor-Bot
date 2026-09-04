from pathlib import Path

from core.tools.file.extractor import extract


UPLOAD_DIR = Path("workspace/uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_file(filename, content):

    path = UPLOAD_DIR / filename


    if isinstance(content, str):

        path.write_text(
            content,
            encoding="utf-8"
        )

    else:

        path.write_bytes(
            content
        )


    return str(path)



def read_document(path):

    return extract(
        path
    )
