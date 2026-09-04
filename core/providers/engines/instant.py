import requests


class InstantSearch:

    name = "duckduckgo_instant"

    def __init__(self):
        self.url = "https://api.duckduckgo.com/"
        self.timeout = 15

    def search(self, query):

        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
            }

            response = requests.get(
                self.url,
                params=params,
                timeout=self.timeout,
                headers={
                    "User-Agent": "VoidClaw-X"
                }
            )

            data = response.json()

            results = []

            if data.get("AbstractText"):

                results.append(
                    {
                        "title": data.get(
                            "Heading",
                            query
                        ),
                        "url": data.get(
                            "AbstractURL",
                            ""
                        ),
                        "snippet": data.get(
                            "AbstractText",
                            ""
                        ),
                    }
                )

            for item in data.get(
                "RelatedTopics",
                []
            ):

                if isinstance(item, dict):

                    if item.get("Text"):

                        results.append(
                            {
                                "title": item.get(
                                    "Text"
                                ),
                                "url": item.get(
                                    "FirstURL",
                                    ""
                                ),
                                "snippet": "",
                            }
                        )

            return results

        except Exception:

            return []
