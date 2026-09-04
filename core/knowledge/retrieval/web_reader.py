import requests
from bs4 import BeautifulSoup


class WebReader:

    def __init__(self):
        self.timeout = 15


    def read(self, url):

        try:

            response = requests.get(
                url,
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


            # حذف الأشياء غير المفيدة
            for tag in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "footer"
                ]
            ):
                tag.decompose()


            text = soup.get_text(
                "\n",
                strip=True
            )


            return {
                "success": True,
                "url": url,
                "content": text[:10000]
            }


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
