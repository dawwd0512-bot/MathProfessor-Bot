from core.providers.engines.html import HTMLSearch
from core.providers.engines.instant import InstantSearch


class SearchProvider:

    def __init__(self):

        self.html = HTMLSearch()
        self.instant = InstantSearch()

    def search(self, query):

        results = self.html.search(query)

        if results:

            return {
                "success": True,
                "query": query,
                "abstract": "",
                "results": results,
            }

        results = self.instant.search(query)

        return {
            "success": True,
            "query": query,
            "abstract": "",
            "results": results,
        }
