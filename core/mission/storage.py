import json
import os


class MissionStorage:

    def __init__(self, path="memory/missions.json"):
        self.path = path

        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, missions):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                missions,
                f,
                ensure_ascii=False,
                indent=4
            )

    def append(self, mission):
        data = self.load()
        data.append(mission)
        self.save(data)

    def clear(self):
        self.save([])
