from dataclasses import dataclass, field
import re
from typing import List, Optional

from core.document_intelligence.document import Document
from core.document_intelligence.structure import (
    DocumentStructure,
    StructureItem,
)


# ============================================================
# INDEXED EXAMPLE
# ============================================================

@dataclass
class IndexedExample:
    number: int
    lesson_number: object
    page_number: int
    text: str


# ============================================================
# INDEXED LESSON
# ============================================================

@dataclass
class IndexedLesson:
    number: Optional[int]
    title: str
    unit_title: Optional[str]
    start_page: int
    end_page: int
    pages: List[int] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)


# ============================================================
# DOCUMENT INDEX
# ============================================================

class DocumentIndex:

    def __init__(
        self,
        document: Document,
        structure: DocumentStructure,
    ):
        self.document = document
        self.structure = structure

        self.lessons: List[IndexedLesson] = []
        self.examples: List[IndexedExample] = []

        self._build()
        self._build_examples()

    # --------------------------------------------------------
    # BUILD
    # --------------------------------------------------------

    def _build(self):
        structure_items = self.structure.items

        lesson_items = [
            item
            for item in structure_items
            if item.kind == "lesson"
        ]

        for index, lesson in enumerate(lesson_items):

            start_page = lesson.page_number

            # ------------------------------------------------
            # Determine where this lesson ends.
            #
            # The boundary is the next STRUCTURE item, not
            # merely the next lesson. This prevents a lesson
            # from consuming a following unit/chapter/section.
            # ------------------------------------------------

            next_boundaries = [
                item.page_number
                for item in structure_items
                if item.page_number > start_page
            ]

            if next_boundaries:
                next_boundary = min(next_boundaries)

                # The logical lesson range ends immediately
                # before the next structural boundary.
                #
                # This is independent from which pages were
                # successfully parsed into the Document.
                end_page = max(
                    start_page,
                    next_boundary - 1,
                )

            else:
                # Use the actual highest page number.
                # document.page_count is only the number of
                # parsed pages and may differ when page numbers
                # contain gaps.
                if self.document.pages:
                    end_page = max(
                        page.number
                        for page in self.document.pages
                    )
                else:
                    end_page = start_page

            pages = [
                page.number
                for page in self.document.pages
                if start_page <= page.number <= end_page
            ]

            unit_title = self._find_unit_for_lesson(
                lesson
            )

            self.lessons.append(
                IndexedLesson(
                    number=lesson.number,
                    title=lesson.title,
                    unit_title=unit_title,
                    start_page=start_page,
                    end_page=end_page,
                    pages=pages,
                )
            )

    # --------------------------------------------------------
    # BUILD EXAMPLE INDEX
    # --------------------------------------------------------

    def _build_examples(self):

        self.examples = []

        for lesson in self.lessons:

            for page_number in lesson.pages:

                page = self.document.get_page(page_number)

                if not page:
                    continue

                text = page.text or ""

                # يدعم Example 1 / Example 10 / EXAMPLE 1
                matches = list(
                    re.finditer(
                        r"(?i)\bExample\s*(\d+)\s*:",
                        text,
                    )
                )

                for i, match in enumerate(matches):

                    number = int(match.group(1))

                    start = match.start()
                    end = (
                        matches[i + 1].start()
                        if i + 1 < len(matches)
                        else len(text)
                    )

                    example_text = text[start:end].strip()

                    if not example_text:
                        continue

                    self.examples.append(
                        IndexedExample(
                            number=number,
                            lesson_number=lesson.number,
                            page_number=page_number,
                            text=example_text,
                        )
                    )

    # --------------------------------------------------------
    # GET EXAMPLE
    # --------------------------------------------------------

    def get_example(
        self,
        lesson_number,
        example_number: int,
    ) -> Optional[IndexedExample]:

        candidates = [
            example
            for example in self.examples
            if str(example.lesson_number).strip() == str(lesson_number).strip()
            and int(example.number) == int(example_number)
        ]

        if not candidates:
            return None

        return candidates[0]

    def get_examples_for_lesson(
        self,
        lesson_number,
    ) -> List[IndexedExample]:

        return [
            example
            for example in self.examples
            if example.lesson_number == lesson_number
        ]

    # --------------------------------------------------------
    # UNIT LOOKUP
    # --------------------------------------------------------

    def _find_unit_for_lesson(
        self,
        lesson: StructureItem,
    ) -> Optional[str]:

        current_unit = None

        for item in self.structure.items:

            if item.kind == "unit":
                current_unit = item.title

            elif item is lesson:
                return current_unit

        return current_unit

    # --------------------------------------------------------
    # GET LESSON
    # --------------------------------------------------------

    def get_lesson(
        self,
        number: int,
        unit_title: Optional[str] = None,
    ) -> Optional[IndexedLesson]:

        # Lesson numbers may be parsed from PDF text as strings
        # such as "5.5", while callers may provide 5.5 as a float.
        # Normalize both sides to strings so decimal lesson numbers
        # like 5.5, 6.1, 6.3 work correctly.
        requested_number = str(number).strip()

        candidates = [
            lesson
            for lesson in self.lessons
            if str(lesson.number).strip() == requested_number
        ]

        if unit_title:
            unit_lower = unit_title.strip().lower()

            candidates = [
                lesson
                for lesson in candidates
                if lesson.unit_title
                and unit_lower in lesson.unit_title.lower()
            ]

        if not candidates:
            return None

        return candidates[0]

    # --------------------------------------------------------
    # SEARCH LESSON BY TITLE
    # --------------------------------------------------------

    def search_lessons(
        self,
        query: str,
    ) -> List[IndexedLesson]:

        query = query.strip().lower()

        if not query:
            return []

        results = []

        for lesson in self.lessons:

            title = lesson.title.lower()

            if query in title:
                results.append(lesson)
                continue

            query_words = {
                word
                for word in query.split()
                if len(word) > 1
            }

            title_words = set(title.split())

            if query_words & title_words:
                results.append(lesson)

        return results

    # --------------------------------------------------------
    # GET PAGE
    # --------------------------------------------------------

    def get_page(
        self,
        page_number: int,
    ):
        return self.document.get_page(
            page_number
        )

    # --------------------------------------------------------
    # GET LESSON TEXT
    # --------------------------------------------------------

    def get_lesson_text(
        self,
        lesson: IndexedLesson,
    ) -> str:

        pages = []

        for page_number in lesson.pages:

            page = self.document.get_page(
                page_number
            )

            if page:
                pages.append(
                    f"[الصفحة {page.number}]\n"
                    f"{page.text}"
                )

        return "\n\n".join(pages)

    # --------------------------------------------------------
    # TABLE OF CONTENTS
    # --------------------------------------------------------

    def table_of_contents(self) -> str:

        lines = []

        current_unit = None

        for lesson in self.lessons:

            if lesson.unit_title != current_unit:

                current_unit = lesson.unit_title

                if current_unit:
                    lines.append(
                        f"📚 {current_unit}"
                    )

            number = (
                str(lesson.number)
                if lesson.number is not None
                else "-"
            )

            if lesson.start_page == lesson.end_page:

                page_text = (
                    f"صفحة {lesson.start_page}"
                )

            else:

                page_text = (
                    f"صفحات "
                    f"{lesson.start_page}-"
                    f"{lesson.end_page}"
                )

            lines.append(
                f"  {number}. "
                f"{lesson.title} "
                f"— {page_text}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def summary(self) -> dict:

        return {
            "filename": self.document.filename,
            "page_count": self.document.page_count,
            "lesson_count": len(self.lessons),
            "lessons": [
                {
                    "number": lesson.number,
                    "title": lesson.title,
                    "unit": lesson.unit_title,
                    "start_page": lesson.start_page,
                    "end_page": lesson.end_page,
                    "pages": lesson.pages,
                }
                for lesson in self.lessons
            ],
        }


# ============================================================
# HELPER
# ============================================================

def build_document_index(
    document: Document,
    structure: DocumentStructure,
) -> DocumentIndex:

    return DocumentIndex(
        document=document,
        structure=structure,
    )
