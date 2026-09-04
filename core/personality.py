import json

def load_personality():
    try:
        with open("config/personality.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "assistant_name": "AI Agent",
            "owner": "",
            "personality": "",
            "rules": []
        }


def build_system_prompt():
    p = load_personality()

    prompt = f"""
اسمك هو {p['assistant_name']}.
مالكك هو {p['owner']}.

الشخصية:
{p['personality']}

القواعد:
"""

    for rule in p["rules"]:
        prompt += f"- {rule}\n"

    return prompt.strip()
