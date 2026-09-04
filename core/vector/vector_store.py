import json
import os


VECTOR_FILE = "workspace/vectors.json"


class VectorStore:

    def __init__(self):

        os.makedirs(
            "workspace",
            exist_ok=True
        )

        if not os.path.exists(VECTOR_FILE):

            with open(
                VECTOR_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    [],
                    f,
                    ensure_ascii=False,
                    indent=2
                )


    def load(self):

        with open(
            VECTOR_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)



    def save(self, data):

        with open(
            VECTOR_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )



    def add(self, text, vector, metadata=None):

        data = self.load()

        data.append(
            {
                "text": text,
                "vector": vector,
                "metadata": metadata or {}
            }
        )

        self.save(data)



    def all(self):

        return self.load()
