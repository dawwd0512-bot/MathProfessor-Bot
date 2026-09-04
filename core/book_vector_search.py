from pathlib import Path

from core.vector_search import VectorSearch


BASE_DIR = Path.home() / "MathProfessor-Bot"
SECTIONS_DIR = BASE_DIR / "data" / "final_sections"


def load_book_sections():
    documents = []

    for path in sorted(SECTIONS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")

        if text.strip():
            documents.append({
                "title": path.stem,
                "text": text,
                "path": str(path),
            })

    return documents


def create_book_search():
    return VectorSearch(load_book_sections())


def search_book(query, top_k=3):
    documents = load_book_sections()
    query_lower = query.lower()

    # Direct title matching
    exact = []

    for doc in documents:
        title = doc["title"].lower()

        if "functions" in query_lower and "functions" in title:
            exact.append({
                **doc,
                "score": 1.0
            })

    if exact:
        remaining = [
            doc for doc in documents
            if doc not in exact
        ]

        search = VectorSearch(remaining)

        results = exact + search.search(query, max(0, top_k - len(exact)))
        return results[:top_k]

    search = VectorSearch(documents)
    return search.search(query, top_k)
