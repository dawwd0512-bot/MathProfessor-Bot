import json
from pathlib import Path


class PersistentRAG:

    def __init__(self):
        self.file_path = (
            Path(__file__).resolve().parent
            / "persistent_documents.json"
        )

        self.documents = {}
        self._load()

    def _load(self):
        if not self.file_path.exists():
            return

        try:
            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as f:
                self.documents = json.load(f)

        except Exception as e:
            print(f"⚠️ تعذر تحميل الملفات المحفوظة: {e}")

    def _save(self):
        temp = self.file_path.with_suffix(".tmp")

        with open(
            temp,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.documents,
                f,
                ensure_ascii=False,
                indent=2
            )

        temp.replace(self.file_path)

    def save_document(self, user_id, content, file_info=None):
        self.documents[str(user_id)] = {
            "content": content,
            "file_info": file_info or {}
        }

        self._save()

    def get_document(self, user_id):
        return self.documents.get(str(user_id))

    def clear(self, user_id):
        self.documents.pop(str(user_id), None)
        self._save()


persistent_rag = PersistentRAG()
