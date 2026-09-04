import os
import uuid


BASE_DIR = "data/uploads"


def create_user_folder(user_id):
    folder = os.path.join(
        BASE_DIR,
        str(user_id)
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    return folder


def save_file(user_id, filename, content):
    folder = create_user_folder(user_id)

    file_id = str(uuid.uuid4())

    path = os.path.join(
        folder,
        f"{file_id}_{filename}"
    )

    with open(
        path,
        "wb"
    ) as f:
        f.write(content)

    return path
