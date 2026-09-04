class KnowledgeExtractor:

    def __init__(self, reader):
        self.reader = reader

    def extract(self, results):

        if not results:
            return ""

        first = results[0]

        url = first.get("url")

        if not url:
            return ""

        text = self.reader.read(url)

        if not text:
            return ""

        return text[:3000]
