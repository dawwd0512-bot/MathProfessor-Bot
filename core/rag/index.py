from typing import List


class DocumentIndex:
    def __init__(self):
        self.documents = {}

    def build(self, user_id: int, chunks: List[str]):
        self.documents[user_id] = chunks

    def clear(self, user_id: int):
        self.documents.pop(user_id, None)

    def count(self, user_id: int):
        return len(self.documents.get(user_id, []))

    def get_all(self, user_id: int):
        return self.documents.get(user_id, [])
