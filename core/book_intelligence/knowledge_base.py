import json
from pathlib import Path


BASE_DIR = Path.home() / "MathProfessor-Bot"
ANALYSIS_DIR = BASE_DIR / "data" / "book_analysis"


class BookKnowledgeBase:

    def __init__(self, analysis_dir=ANALYSIS_DIR):
        self.analysis_dir = Path(analysis_dir)
        self.index = self._load_json("index.json")

    def _load_json(self, filename):
        path = self.analysis_dir / filename

        if not path.exists():
            return None

        return json.loads(
            path.read_text(encoding="utf-8")
        )

    def sections(self):
        return self.index or []

    def get_section(self, section_index):
        if section_index < 1:
            return None

        matches = list(
            self.analysis_dir.glob(
                f"section_{section_index}_*.json"
            )
        )

        if not matches:
            return None

        return json.loads(
            matches[0].read_text(encoding="utf-8")
        )

    def search(self, query):
        query = query.strip().lower()

        results = []

        for i, section in enumerate(self.sections(), start=1):
            title = str(section.get("title", ""))

            if query in title.lower():
                data = self.get_section(i)

                if data:
                    results.append({
                        "section": i,
                        "number": data.get("number"),
                        "title": data.get("title"),
                        "summary": data.get("summary", ""),
                        "formulas": data.get("formulas", ""),
                        "mind_map": data.get("mind_map", ""),
                        "questions": data.get("questions", ""),
                    })

        return results

    def get_all_sections(self):
        results = []

        for i in range(1, len(self.sections()) + 1):
            data = self.get_section(i)

            if data:
                results.append(data)

        return results


def create_knowledge_base():
    return BookKnowledgeBase()
