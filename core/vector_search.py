import re
import math
from pathlib import Path
import json
import numpy as np


class VectorSearch:
    def __init__(self, documents):
        self.documents = documents
        self.vectors = self._build_vectors(documents)

    def _tokens(self, text):
        return re.findall(r'[\w\u0600-\u06FF]+', text.lower())

    def _vector(self, text):
        tokens = self._tokens(text)

        if not tokens:
            return np.zeros(512, dtype=np.float32)

        vector = np.zeros(512, dtype=np.float32)

        for token in tokens:
            index = hash(token) % 512
            vector[index] += 1.0

        norm = np.linalg.norm(vector)

        if norm:
            vector /= norm

        return vector

    def _build_vectors(self, documents):
        return np.array(
            [self._vector(doc["text"]) for doc in documents],
            dtype=np.float32
        )

    def search(self, query, top_k=5):
        if not self.documents:
            return []

        q = self._vector(query)

        scores = self.vectors @ q
        indexes = np.argsort(scores)[::-1][:top_k]

        results = []

        for i in indexes:
            results.append({
                **self.documents[int(i)],
                "score": float(scores[int(i)])
            })

        return results
