import requests
from bs4 import BeautifulSoup


class WebReader:

    def __init__(self):
        self.timeout = 20

    def read(self, url):

        try:

            response = requests.get(
                url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            soup = BeautifulSoup(
                response.text,
                "lxml"
            )

            for tag in soup([
                "script",
                "style",
                "noscript",
                "header",
                "footer",
                "nav",
                "aside",
            ]):
                tag.decompose()

            text = soup.get_text(
                separator="\n",
                strip=True
            )

            lines = []

            for line in text.splitlines():

                line = line.strip()

                if line:

                    lines.append(line)

            return "\n".join(lines)

        except Exception:

            return ""
