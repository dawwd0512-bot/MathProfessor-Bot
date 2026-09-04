import time
import requests

from core.config import Config
from core.personality import build_system_prompt
from core.history import build_history


class LLM:
    def __init__(self):
        self.provider = Config.DEFAULT_PROVIDER

    def ask(self, prompt, user_id=None, system=None):
        if system is None:
            system = build_system_prompt()

        if self.provider == "gemini":
            return self._gemini(prompt, system, user_id)

        if self.provider == "openrouter":
            return self._openrouter(prompt, system)

        return "Provider غير مدعوم."

    def _gemini(self, prompt, system, user_id=None):
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{Config.GEMINI_MODEL}:generateContent"
            f"?key={Config.GEMINI_API_KEY}"
        )

        history = ""
        if user_id is not None:
            history = build_history(user_id)

        full_prompt = f"""
{system}

المحادثة السابقة:
{history}

المستخدم:
{prompt}
"""

        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_prompt
                        }
                    ]
                }
            ]
        }

        last_error = None

        for _ in range(3):
            try:
                r = requests.post(
                    url,
                    json=body,
                    timeout=120
                )

                if r.status_code == 200:
                    data = r.json()

                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except Exception:
                        return str(data)

                if r.status_code in (429, 503):
                    time.sleep(3)
                    continue

                return f"Gemini Error:\n{r.text}"

            except Exception as e:
                last_error = e
                time.sleep(3)

        return f"Gemini Connection Error:\n{last_error}"

    def _openrouter(self, prompt, system):
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        body = {
            "model": Config.OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 7000
        }

        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=120
            )

        except Exception as e:
            return f"OpenRouter Connection Error:\n{e}"

        if r.status_code != 200:
            return f"OpenRouter Error:\n{r.text}"

        data = r.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return str(data)
