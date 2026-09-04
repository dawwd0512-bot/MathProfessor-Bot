import requests
from bs4 import BeautifulSoup


class HTMLSearch:

    name = "duckduckgo_html"

    def __init__(self):
        self.url = "https://html.duckduckgo.com/html/"
        self.timeout = 15

    def search(self, query):

        try:
            response = requests.post(
                self.url,
                data={
                    "q": query
                },
                timeout=self.timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "VoidClaw-X"
                    )
                }
            )

            soup = BeautifulSoup(
                response.text,
                "lxml"
            )

            results = []

            for item in soup.select(
                ".result"
            ):

                title = item.select_one(
                    ".result__title"
                )

                link = item.select_one(
                    ".result__a"
                )

                snippet = item.select_one(
                    ".result__snippet"
                )

                if link:

                    results.append(
                        {
                            "title": (
                                title.get_text(
                                    " ",
                                    strip=True
                                )
                                if title
                                else link.get_text(
                                    " ",
                                    strip=True
                                )
                            ),
                            "url": link.get(
                                "href",
                                ""
                            ),
                            "snippet": (
                                snippet.get_text(
                                    " ",
                                    strip=True
                                )
                                if snippet
                                else ""
                            ),
                        }
                    )

            return results

        except Exception:

            return []
