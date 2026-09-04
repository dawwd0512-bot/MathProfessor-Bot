import re
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# PAGE
# ============================================================

@dataclass
class DocumentPage:
    number: int
    text: str

    @property
    def title_candidates(self) -> List[str]:
        """
        استخراج مرشحات أولية للعناوين من بداية الصفحة.
        لا نحكم هنا أن السطر عنوان بشكل نهائي.
        """
        candidates = []

        for line in self.text.splitlines():
            line = line.strip()

            if not line:
                continue

            if len(line) > 120:
                continue

            candidates.append(line)

            if len(candidates) >= 8:
                break

        return candidates


# ============================================================
# DOCUMENT
# ============================================================

@dataclass
class Document:
    pages: List[DocumentPage] = field(default_factory=list)
    filename: Optional[str] = None

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def get_page(
        self,
        page_number: int,
    ) -> Optional[DocumentPage]:

        for page in self.pages:
            if page.number == page_number:
                return page

        return None

    def all_text(self) -> str:
        return "\n\n".join(
            f"[الصفحة {page.number}]\n{page.text}"
            for page in self.pages
        )


# ============================================================
# DOCUMENT PARSER
# ============================================================

class DocumentParser:

    # Supports both formats:
    #
    # [الصفحة 1]
    #
    # and:
    #
    # --- PAGE 1 ---
    #
    PAGE_PATTERN = re.compile(
        r"(?:\[الصفحة\s+(\d+)\]|---\s*PAGE\s+(\d+)\s*---)",
        re.IGNORECASE,
    )

    def parse(
        self,
        text: str,
        filename: Optional[str] = None,
    ) -> Document:

        if not text or not text.strip():
            return Document(
                pages=[],
                filename=filename,
            )

        matches = list(
            self.PAGE_PATTERN.finditer(text)
        )

        pages = []

        # ----------------------------------------------------
        # PDF text already contains page markers
        #
        # Supported:
        # [الصفحة 1]
        # --- PAGE 1 ---
        # ----------------------------------------------------

        if matches:

            for index, match in enumerate(matches):

                # Group 1 = [الصفحة N]
                # Group 2 = --- PAGE N ---
                page_number = int(
                    match.group(1) or match.group(2)
                )

                start = match.end()

                if index + 1 < len(matches):
                    end = matches[index + 1].start()
                else:
                    end = len(text)

                page_text = text[start:end].strip()

                pages.append(
                    DocumentPage(
                        number=page_number,
                        text=page_text,
                    )
                )

        # ----------------------------------------------------
        # Generic document without page markers
        # ----------------------------------------------------

        else:

            pages.append(
                DocumentPage(
                    number=1,
                    text=text.strip(),
                )
            )

        return Document(
            pages=pages,
            filename=filename,
        )


# ============================================================
# HELPERS
# ============================================================

def parse_document(
    text: str,
    filename: Optional[str] = None,
) -> Document:

    parser = DocumentParser()

    return parser.parse(
        text=text,
        filename=filename,
    )
