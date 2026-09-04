import json
from pathlib import Path

from core.book_intelligence.pdf_reader import extract_pdf_text
from core.book_intelligence.chapter_detector import detect_chapters
from core.book_intelligence.book_analyzer import create_gemini_book_analyzer


BASE_DIR = Path.home() / "MathProfessor-Bot"

PDF = (
    BASE_DIR
    / "data/uploads/"
    / "6542816215_Calculus 1_By Dr.Ahmed M. El-Ashqar (1) (3).pdf"
)

OUTPUT_DIR = BASE_DIR / "data/book_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    print("📖 Reading PDF...")

    text = extract_pdf_text(str(PDF))
    sections = detect_chapters(text)

    print(f"📚 Sections: {len(sections)}")

    analyzer = create_gemini_book_analyzer()

    # ========================================================
    # INDEX
    # ========================================================

    index = []

    for i, section in enumerate(sections, start=1):
        index.append({
            "file_number": i,
            "number": section.number,
            "title": section.title,
            "characters": len(section.text),
            "file": f"section_{i}_{section.number}.json",
        })

    save_json(
        OUTPUT_DIR / "index.json",
        index,
    )

    print("✅ Index saved.")

    # ========================================================
    # EACH SECTION = INDEPENDENT FILE
    # ========================================================

    for i, section in enumerate(sections, start=1):

        print()
        print("=" * 60)
        print(f"📘 [{i}/{len(sections)}] {section.title}")
        print(f"Characters: {len(section.text)}")
        print("=" * 60)

        # ----------------------------------------------------
        # ORIGINAL TEXT
        # ----------------------------------------------------

        original_text = section.text

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print("📝 Summary...")
        summary = analyzer.summarize_chapter(section)

        # ----------------------------------------------------
        # FORMULAS
        # ----------------------------------------------------

        print("📐 Formulas...")
        formulas = analyzer.extract_formulas(original_text)

        # ----------------------------------------------------
        # MIND MAP
        # ----------------------------------------------------

        print("🧠 Mind map...")
        mind_map = analyzer.create_mind_map(original_text)

        # ----------------------------------------------------
        # QUESTIONS
        # ----------------------------------------------------

        print("❓ Questions...")
        questions = analyzer.generate_questions(
            original_text,
            count=10,
        )

        # ----------------------------------------------------
        # COMPLETE SECTION FILE
        # ----------------------------------------------------

        result = {
            "section": {
                "number": section.number,
                "title": section.title,
                "characters": len(original_text),
            },

            # النص الأصلي كما استخرج من الكتاب
            "original_text": original_text,

            # شرح القسم
            "explanation": summary,

            # القوانين والتعريفات
            "formulas": formulas,

            # الخريطة الذهنية
            "mind_map": mind_map,

            # الأسئلة
            "questions": questions,
        }

        filename = (
            f"section_{i}_{section.number}.json"
        )

        output_file = OUTPUT_DIR / filename

        save_json(
            output_file,
            result,
        )

        print(f"💾 Saved: {output_file}")

    print()
    print("=" * 60)
    print("🎉 BOOK INTELLIGENCE COMPLETE")
    print(f"📚 Total sections: {len(sections)}")
    print(f"📂 Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
