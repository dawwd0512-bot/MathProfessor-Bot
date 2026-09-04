import subprocess
import sys

def open_url(url):
    subprocess.run(["termux-open-url", url], check=False)

def open_app(package):
    urls = {
        "com.google.android.youtube": "https://www.youtube.com"
    }

    url = urls.get(package)
    if not url:
        return False

    result = subprocess.run(
        ["termux-open-url", url],
        check=False
    )
    return result.returncode == 0
