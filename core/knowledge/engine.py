from core.extractor.knowledge_extractor import KnowledgeExtractor
from core.providers.search import SearchProvider
from core.tools.readers.web_reader import WebReader


class KnowledgeEngine:

    def __init__(self):

        self.search = SearchProvider()

        self.reader = WebReader()

        self.extractor = KnowledgeExtractor(
            self.reader
        )

    def search_text(self, query):

        result = self.search.search(query)

        if not result.get("success"):

            return ""

        return self.extractor.extract(
            result["results"]
        )
