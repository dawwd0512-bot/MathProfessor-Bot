import json
from pathlib import Path


class StateManager:

    def __init__(self, path="memory/agent_state.json"):

        self.path = Path(path)

        self.path.parent.mkdir(
            exist_ok=True
        )

        if not self.path.exists():

            self.save({})


    def save(self, data):

        with open(
            self.path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )


    def load(self):

        try:

            with open(
                self.path,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:

            return {}


    def update(self, key, value):

        data = self.load()

        data[key] = value

        self.save(data)

        return data
