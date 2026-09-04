import hashlib


class EmbeddingEngine:

    def __init__(self):
        pass


    def embed(self, text):

        if not isinstance(text, str):
            text = str(text)


        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()


        vector = []

        for i in range(0, len(digest), 2):

            value = int(
                digest[i:i+2],
                16
            )

            vector.append(
                value / 255
            )


        return vector



def embed_text(text):

    engine = EmbeddingEngine()

    return engine.embed(text)
