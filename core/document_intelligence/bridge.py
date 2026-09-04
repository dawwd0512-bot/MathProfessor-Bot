from typing import List, Optional

from core.document_intelligence.document import (
    Document,
    parse_document,
)
from core.document_intelligence.structure import (
    analyze_document_structure,
)
from core.document_intelligence.index import (
    DocumentIndex,
    build_document_index,
)


class DocumentIntelligenceBridge:

    def __init__(self):
        self.documents = {}

    def build(
        self,
        user_id: int,
        text: str,
        filename: Optional[str] = None,
    ) -> DocumentIndex:

        document = parse_document(
            text=text,
            filename=filename,
        )

        structure = analyze_document_structure(
            document
        )

        index = build_document_index(
            document,
            structure,
        )

        self.documents[str(user_id)] = index

        return index

    def get(
        self,
        user_id: int,
    ) -> Optional[DocumentIndex]:

        return self.documents.get(
            str(user_id)
        )

    def clear(
        self,
        user_id: int,
    ):

        self.documents.pop(
            str(user_id),
            None,
        )

    def search_lessons(
        self,
        user_id: int,
        query: str,
    ) -> List:

        index = self.get(user_id)

        if not index:
            return []

        return index.search_lessons(
            query
        )

    def get_lesson(
        self,
        user_id: int,
        number: int,
        unit_title: Optional[str] = None,
    ):

        index = self.get(user_id)

        if not index:
            return None

        return index.get_lesson(
            number=number,
            unit_title=unit_title,
        )

    def get_example(
        self,
        user_id: int,
        lesson_number,
        example_number: int,
    ):

        index = self.get(user_id)

        if not index:
            return None

        return index.get_example(
            lesson_number=lesson_number,
            example_number=example_number,
        )

    def get_lesson_text(
        self,
        user_id: int,
        lesson,
    ) -> str:

        index = self.get(user_id)

        if not index:
            return ""

        return index.get_lesson_text(
            lesson
        )

    def table_of_contents(
        self,
        user_id: int,
    ) -> str:

        index = self.get(user_id)

        if not index:
            return ""

        return index.table_of_contents()


document_bridge = DocumentIntelligenceBridge()
