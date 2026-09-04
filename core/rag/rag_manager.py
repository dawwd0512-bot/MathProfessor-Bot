from typing import Optional

from core.rag.chunker import TextChunker
from core.rag.index import DocumentIndex
from core.rag.search import ChunkSearcher

from core.document_intelligence.bridge import document_bridge


class RAGManager:

    def __init__(self):
        self.chunker = TextChunker()
        self.index = DocumentIndex()
        self.searcher = ChunkSearcher()

    # ========================================================
    # LOAD DOCUMENT
    # ========================================================

    def load_document(
        self,
        user_id: int,
        text: str,
        filename: Optional[str] = None,
    ):
        # ----------------------------------------------------
        # Legacy RAG
        # ----------------------------------------------------

        chunks = self.chunker.split(text)

        self.index.build(
            user_id,
            chunks,
        )

        # ----------------------------------------------------
        # Document Intelligence
        # ----------------------------------------------------

        document_index = document_bridge.build(
            user_id=user_id,
            text=text,
            filename=filename,
        )

        return {
            "chunks": len(chunks),
            "pages": document_index.document.page_count,
            "lessons": len(document_index.lessons),
        }

    # ========================================================
    # LEGACY CHUNK SEARCH
    # ========================================================

    def search(
        self,
        user_id: int,
        question: str,
    ):
        return self.searcher.search(
            question,
            self.index.get_all(user_id),
        )

    # ========================================================
    # DOCUMENT INTELLIGENCE
    # ========================================================

    def search_lessons(
        self,
        user_id: int,
        query: str,
    ):
        return document_bridge.search_lessons(
            user_id=user_id,
            query=query,
        )

    def get_lesson(
        self,
        user_id: int,
        number: int,
        unit_title: Optional[str] = None,
    ):
        return document_bridge.get_lesson(
            user_id=user_id,
            number=number,
            unit_title=unit_title,
        )

    def get_example(
        self,
        user_id: int,
        lesson_number,
        example_number: int,
    ):

        return document_bridge.get_example(
            user_id=user_id,
            lesson_number=lesson_number,
            example_number=example_number,
        )

    def get_lesson_text(
        self,
        user_id: int,
        lesson,
    ) -> str:
        return document_bridge.get_lesson_text(
            user_id=user_id,
            lesson=lesson,
        )

    def table_of_contents(
        self,
        user_id: int,
    ) -> str:
        return document_bridge.table_of_contents(
            user_id=user_id,
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
        user_id: int,
    ):
        self.index.clear(user_id)
        document_bridge.clear(user_id)


rag_manager = RAGManager()
