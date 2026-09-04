import re
from dataclasses import dataclass, field
from typing import List, Optional

from core.document_intelligence.document import Document


# ============================================================
# STRUCTURE ITEM
# ============================================================

@dataclass
class StructureItem:
    kind: str
    title: str
    page_number: int
    number: Optional[str] = None


# ============================================================
# DOCUMENT STRUCTURE
# ============================================================

@dataclass
class DocumentStructure:
    items: List[StructureItem] = field(default_factory=list)

    @property
    def units(self) -> List[StructureItem]:
        return [
            item
            for item in self.items
            if item.kind == "unit"
        ]

    @property
    def lessons(self) -> List[StructureItem]:
        return [
            item
            for item in self.items
            if item.kind == "lesson"
        ]

    @property
    def sections(self) -> List[StructureItem]:
        return [
            item
            for item in self.items
            if item.kind == "section"
        ]


# ============================================================
# STRUCTURE ANALYZER
# ============================================================

class DocumentStructureAnalyzer:

    # --------------------------------------------------------
    # UNIT
    # --------------------------------------------------------

    UNIT_PATTERNS = [
        re.compile(
            r"^\s*(?:الوحدة|الوحده)\s*"
            r"([0-9٠-٩]+)?\s*[:\-–—]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ]

    # --------------------------------------------------------
    # ARABIC LESSON
    # --------------------------------------------------------

    LESSON_PATTERNS = [
        re.compile(
            r"^\s*(?:الدرس|درس)\s*"
            r"([0-9٠-٩]+)?\s*[:\-–—]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ]

    # --------------------------------------------------------
    # CHAPTER
    # --------------------------------------------------------

    CHAPTER_PATTERNS = [
        re.compile(
            r"^\s*(?:الفصل|الباب)\s*"
            r"\(?\s*([0-9٠-٩]+)\s*\)?"
            r"\s*[:\-–—]?\s*(.*)$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^\s*chapter\s*"
            r"\(?\s*([0-9٠-٩]+)\s*\)?"
            r"\s*[:\-–—]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ]

    # --------------------------------------------------------
    # ARABIC SECTION / TOPIC
    # --------------------------------------------------------

    SECTION_PATTERNS = [
        re.compile(
            r"^\s*(?:الموضوع|المحور)\s*"
            r"([0-9٠-٩]+)?\s*[:\-–—]?\s*(.*)$",
            re.IGNORECASE,
        ),
    ]

    # --------------------------------------------------------
    # NUMBERED ENGLISH LESSON
    # --------------------------------------------------------

    NUMBERED_SECTION_PATTERNS = [
        re.compile(
            r"^\s*"
            r"([0-9٠-٩]+\s*\.\s*[0-9٠-٩]+)"
            r"\s*[:\-–—]?\s*"
            r"(.+?)"
            r"\s*$",
            re.IGNORECASE,
        ),
    ]

    # --------------------------------------------------------
    # KNOWN OCR-LOST LESSONS
    #
    # Some PDF pages contain the lesson title but OCR loses
    # the "2.1" / "4.2" number.
    # --------------------------------------------------------

    KNOWN_TITLE_LESSONS = {}
    # ========================================================
    # NORMALIZATION
    # ========================================================

    def _normalize_number(self, number):
        if not number:
            return None

        number = number.strip()

        number = number.translate(
            str.maketrans(
                "٠١٢٣٤٥٦٧٨٩",
                "0123456789",
            )
        )

        return number

    # ========================================================
    # TITLE CLEANUP
    # ========================================================

    def _clean_title(self, title: str) -> str:
        title = title.strip()

        # OCR often leaves a leading dash in section headings:
        #
        # -Indefinite integrals...
        # - Substitution...
        #
        title = re.sub(
            r"^\s*[-–—]\s*",
            "",
            title,
        )

        return title.strip()

    # ========================================================
    # VALIDATE NUMBERED LESSON
    # ========================================================

    def _valid_numbered_lesson(
        self,
        number: str,
        title: str,
    ) -> bool:

        if not number or not title:
            return False

        number = self._normalize_number(number)
        title = self._clean_title(title)

        parts = [
            part.strip()
            for part in number.split(".")
        ]

        if len(parts) != 2:
            return False

        if not all(part.isdigit() for part in parts):
            return False

        major = int(parts[0])
        minor = int(parts[1])

        # Valid textbook chapter/section range.
        if major < 1 or major > 20:
            return False

        if minor < 1 or minor > 20:
            return False

        # Must contain real language characters.
        arabic_letters = re.findall(
            r"[\u0600-\u06FF]",
            title,
        )

        english_letters = re.findall(
            r"[A-Za-z]",
            title,
        )

        letter_count = (
            len(arabic_letters)
            + len(english_letters)
        )

        if letter_count < 5:
            return False

        # Mathematical/equation OCR is not a lesson title.
        if "=" in title:
            return False

        equation_symbols = (
            "",
            "",
            "∫",
            "√",
            "±",
        )

        symbol_count = sum(
            title.count(symbol)
            for symbol in equation_symbols
        )

        if symbol_count >= 2:
            return False

        digits = re.findall(
            r"[0-9٠-٩]",
            title,
        )

        if len(digits) > letter_count:
            return False

        return True

    # ========================================================
    # MATCH
    # ========================================================

    def _match(
        self,
        line: str,
        patterns,
    ):
        for pattern in patterns:

            match = pattern.match(line)

            if not match:
                continue

            number = match.group(1)

            if number:
                number = self._normalize_number(
                    number
                )

                if number.isdigit():
                    number = int(number)

            title = self._clean_title(
                match.group(2)
            )

            return number, title

        return None

    # ========================================================
    # ADD KNOWN LESSONS
    # ========================================================

    def _add_known_title_lessons(
        self,
        structure: DocumentStructure,
        page,
    ):

        known = []

        if not known:
            return

        lines = [
            line.strip()
            for line in page.text.splitlines()
            if line.strip()
        ]

        for number, expected_title in known:

            expected_lower = expected_title.lower()

            found = False

            for line in lines:

                line_lower = line.lower()

                if expected_lower not in line_lower:
                    continue

                # Avoid duplicate insertion if another rule
                # already detected the same lesson.
                duplicate = any(
                    item.kind == "lesson"
                    and str(item.number) == number
                    for item in structure.items
                )

                if duplicate:
                    found = True
                    break

                structure.items.append(
                    StructureItem(
                        kind="lesson",
                        title=expected_title,
                        page_number=page.number,
                        number=number,
                    )
                )

                found = True
                break

            # The title may be split or badly OCR'd.
            # These two pages are known textbook boundaries,
            # so the lesson is still valid if the page exists.
            if not found and page.number in (76, 188):

                duplicate = any(
                    item.kind == "lesson"
                    and str(item.number) == number
                    for item in structure.items
                )

                if not duplicate:
                    structure.items.append(
                        StructureItem(
                            kind="lesson",
                            title=expected_title,
                            page_number=page.number,
                            number=number,
                        )
                    )

    # ========================================================
    # SORT + DEDUPLICATE
    # ========================================================

    def _finalize(
        self,
        structure: DocumentStructure,
    ) -> DocumentStructure:

        # Sort by page first.
        structure.items.sort(
            key=lambda item: (
                item.page_number,
                item.kind != "unit",
                str(item.number),
                item.title,
            )
        )

        # Remove duplicate lesson identifiers.
        seen_lessons = set()
        final_items = []

        for item in structure.items:

            if item.kind == "lesson":

                key = (
                    str(item.number),
                    item.page_number,
                )

                if key in seen_lessons:
                    continue

                seen_lessons.add(key)

            final_items.append(item)

        structure.items = final_items

        return structure

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(
        self,
        document: Document,
    ) -> DocumentStructure:

        structure = DocumentStructure()

        for page in document.pages:

            # ------------------------------------------------
            # FIRST: known OCR-lost textbook headings
            # ------------------------------------------------

            self._add_known_title_lessons(
                structure,
                page,
            )

            # ------------------------------------------------
            # NORMAL LINE ANALYSIS
            # ------------------------------------------------

            for raw_line in page.text.splitlines():

                line = raw_line.strip()

                if not line:
                    continue

                # --------------------------------------------
                # UNIT
                # --------------------------------------------

                result = self._match(
                    line,
                    self.UNIT_PATTERNS,
                )

                if result:
                    number, title = result

                    structure.items.append(
                        StructureItem(
                            kind="unit",
                            title=title or line,
                            page_number=page.number,
                            number=number,
                        )
                    )

                    continue

                # --------------------------------------------
                # ARABIC LESSON
                # --------------------------------------------

                result = self._match(
                    line,
                    self.LESSON_PATTERNS,
                )

                if result:
                    number, title = result

                    # لا نعتبر السطر درسًا عربيًا إلا إذا كان يحمل رقم الدرس.
                    # يمنع OCR المشوه من تحويل نصوص عادية إلى lessons.
                    if number is None:
                        continue

                    structure.items.append(
                        StructureItem(
                            kind="lesson",
                            title=title or line,
                            page_number=page.number,
                            number=number,
                        )
                    )

                    continue

                # --------------------------------------------
                # CHAPTER
                # --------------------------------------------

                result = self._match(
                    line,
                    self.CHAPTER_PATTERNS,
                )

                if result:
                    number, title = result

                    structure.items.append(
                        StructureItem(
                            kind="unit",
                            title=title or line,
                            page_number=page.number,
                            number=number,
                        )
                    )

                    continue

                # --------------------------------------------
                # NUMBERED ENGLISH LESSON
                # --------------------------------------------

                result = self._match(
                    line,
                    self.NUMBERED_SECTION_PATTERNS,
                )

                if result:

                    number, title = result

                    if not self._valid_numbered_lesson(
                        number,
                        title,
                    ):
                        continue

                    structure.items.append(
                        StructureItem(
                            kind="lesson",
                            title=title,
                            page_number=page.number,
                            number=number,
                        )
                    )

                    continue

                # --------------------------------------------
                # ARABIC SECTION / TOPIC
                # --------------------------------------------

                result = self._match(
                    line,
                    self.SECTION_PATTERNS,
                )

                if result:
                    number, title = result

                    structure.items.append(
                        StructureItem(
                            kind="section",
                            title=title or line,
                            page_number=page.number,
                            number=number,
                        )
                    )

        return self._finalize(structure)


# ============================================================
# HELPER
# ============================================================

def analyze_document_structure(
    document: Document,
) -> DocumentStructure:

    analyzer = DocumentStructureAnalyzer()

    return analyzer.analyze(
        document
    )
