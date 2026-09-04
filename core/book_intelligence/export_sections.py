import json
import re
from pathlib import Path

BASE_DIR = Path.home() / "MathProfessor-Bot"
INPUT_DIR = BASE_DIR / "data/book_analysis"
OUTPUT_DIR = BASE_DIR / "data/final_sections"
IMAGE_DIR = BASE_DIR / "data/generated_images"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def make_number_line(number, title):
    path = IMAGE_DIR / f"section_{number}_number_line.svg"

    width = 900
    height = 180

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<line x1="70" y1="95" x2="830" y2="95" stroke="black" stroke-width="3"/>',
        '<polygon points="830,95 815,87 815,103" fill="black"/>',
        f'<text x="450" y="35" text-anchor="middle" font-size="24" '
        f'font-family="Arial" font-weight="bold">{title} — Number Line / خط الأعداد</text>',
    ]

    for n in range(-5, 6):
        x = 70 + (n + 5) * 76

        svg.append(
            f'<line x1="{x}" y1="83" x2="{x}" y2="107" '
            'stroke="black" stroke-width="2"/>'
        )

        svg.append(
            f'<text x="{x}" y="135" text-anchor="middle" '
            f'font-size="18" font-family="Arial">{n}</text>'
        )

    svg.append("</svg>")

    path.write_text("\n".join(svg), encoding="utf-8")
    return path


def make_function_graph(number):
    try:
        from core.image_generator import generate_function_graph

        return Path(
            generate_function_graph(
                "x**2",
                f"section_{number}_function.svg"
            )
        )

    except Exception as e:
        print("⚠️ function graph:", e)
        return None


def make_mind_map(number, title, summary, formulas):
    """
    Mind map SVG حقيقية، بدون مكتبات إضافية.
    """
    path = IMAGE_DIR / f"section_{number}_mind_map.svg"

    center_x = 450
    center_y = 250

    branches = []

    if summary:
        branches.append(("الشرح", str(summary)[:90]))

    if formulas:
        branches.append(("القوانين", str(formulas)[:90]))

    if not branches:
        branches = [
            ("المفاهيم", title),
            ("التطبيق", "أمثلة وتمارين"),
        ]

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>',
        '.box{fill:#f4f4f4;stroke:#222;stroke-width:2}',
        '.text{font-family:Arial;font-size:18px}',
        '</style>',
    ]

    # المركز
    svg.append(
        f'<rect x="300" y="200" width="300" height="90" rx="20" class="box"/>'
    )

    svg.append(
        f'<text x="{center_x}" y="255" text-anchor="middle" '
        f'class="text" font-weight="bold">{title}</text>'
    )

    positions = [
        (40, 80),
        (560, 80),
        (40, 350),
        (560, 350),
    ]

    for i, (label, text) in enumerate(branches[:4]):
        x, y = positions[i]

        svg.append(
            f'<line x1="{center_x}" y1="{center_y}" '
            f'x2="{x + 140}" y2="{y + 35}" '
            f'stroke="#555" stroke-width="3"/>'
        )

        svg.append(
            f'<rect x="{x}" y="{y}" width="280" height="75" '
            f'rx="15" class="box"/>'
        )

        svg.append(
            f'<text x="{x + 140}" y="{y + 28}" '
            f'text-anchor="middle" class="text" font-weight="bold">'
            f'{label}</text>'
        )

        clean = re.sub(r"<[^>]+>", "", text)
        clean = clean.replace("&", "و")[:35]

        svg.append(
            f'<text x="{x + 140}" y="{y + 52}" '
            f'text-anchor="middle" class="text">{clean}</text>'
        )

    svg.append("</svg>")

    path.write_text("\n".join(svg), encoding="utf-8")
    return path


def main():
    files = sorted(INPUT_DIR.glob("section_*.json"))

    if not files:
        print("❌ لا توجد ملفات أقسام.")
        return

    for file in files:
        data = json.loads(
            file.read_text(encoding="utf-8")
        )

        number = data.get("number", "")
        title = data.get("title", "Section")

        original = data.get("original_text", "")
        summary = data.get("summary", "")
        formulas = data.get("formulas", "")
        mind_map = data.get("mind_map", "")
        questions = data.get("questions", "")

        # كل محتوى القسم
        all_text = "\n".join([
            str(title or ""),
            str(original or ""),
            str(summary or ""),
            str(formulas or ""),
            str(mind_map or ""),
            str(questions or ""),
        ]).lower()

        images = []

        # خط أعداد
        if any(x in all_text for x in [
            "number line",
            "real line",
            "real numbers",
            "خط الأعداد",
            "الأعداد الحقيقية",
        ]):
            images.append(
                make_number_line(number, title)
            )

        # رسم دالة
        if any(x in all_text for x in [
            "function",
            "functions",
            "دالة",
            "الدوال",
            "graph",
            "رسم بياني",
            "parabola",
        ]):
            image = make_function_graph(number)

            if image:
                images.append(image)

        # Mind Map لكل قسم
        images.append(
            make_mind_map(
                number,
                title,
                summary,
                formulas
            )
        )

        safe_title = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in title
        ).strip()

        output = OUTPUT_DIR / (
            f"section_{number}_{safe_title}.md"
        )

        image_links = "\n".join(
            f"![Visual]({image.relative_to(BASE_DIR / 'data')})"
            for image in images
            if image and image.exists()
        )

        content = f"""# {title}

## 🧠 الخريطة الذهنية

{image_links}

---

## 📚 الشرح والملخص

{summary}

---

## 📐 القوانين والتعريفات

{formulas}

---

## 📝 الأسئلة والتمارين

{questions}

---

## النص الأصلي

{original}

---

## الخريطة الذهنية النصية

{mind_map}
"""

        output.write_text(
            content,
            encoding="utf-8"
        )

        print(f"✅ {output.name}")

        for image in images:
            if image and image.exists():
                print(f"   🖼️ {image.name}")

    print()
    print("🎉 FINAL EXPORT COMPLETE")
    print(f"📂 {OUTPUT_DIR}")
    print(f"🖼️ {IMAGE_DIR}")


if __name__ == "__main__":
    main()
