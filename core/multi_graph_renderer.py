from pathlib import Path
import re
import sympy as sp

from core.image_generator import generate_function_graph

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "data" / "generated_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

COLORS = [
    "#2563eb",
    "#16a34a",
    "#9333ea",
    "#ea580c",
    "#0891b2",
    "#db2777",
]


def _split(expressions):
    if isinstance(expressions, str):
        expressions = (
            expressions
            .replace("،", ",")
            .replace(" و ", ",")
            .split(",")
        )
    return [str(x).strip() for x in expressions if str(x).strip()]


def _intersection_points(expressions):
    x = sp.Symbol("x")
    parsed = []

    locals_map = {
        "x": x,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "sqrt": sp.sqrt,
        "log": sp.log,
        "ln": sp.log,
        "exp": sp.exp,
        "pi": sp.pi,
        "e": sp.E,
    }

    for expression in expressions:
        text = expression.strip()

        if "=" in text:
            left, right = text.split("=", 1)
            if left.strip().lower() == "y":
                text = right.strip()

        text = (
            text.replace("²", "**2")
            .replace("³", "**3")
            .replace("×", "*")
            .replace("÷", "/")
            .replace("^", "**")
        )

        expr = sp.sympify(text, locals=locals_map)
        parsed.append(expr)

    points = []

    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            try:
                solutions = sp.solve(
                    sp.Eq(parsed[i], parsed[j]),
                    x
                )

                for xv in solutions:
                    if xv.is_real is False:
                        continue

                    xv_num = float(sp.N(xv))

                    if not -10 <= xv_num <= 10:
                        continue

                    yv = parsed[i].subs(x, xv)
                    yv_num = float(sp.N(yv))

                    if not -10 <= yv_num <= 10:
                        continue

                    point = (round(xv_num, 8), round(yv_num, 8))

                    if point not in points:
                        points.append(point)

            except Exception:
                continue

    return points


def generate_multi_function_graph(expressions, filename="multi_function.svg"):
    expressions = _split(expressions)

    if not expressions:
        raise ValueError("لم يتم العثور على دوال للرسم.")

    if len(expressions) == 1:
        return generate_function_graph(expressions[0], filename)

    generated = []

    for index, expression in enumerate(expressions):
        temp_name = f"_multi_tmp_{index}.svg"
        temp_path = generate_function_graph(expression, temp_name)
        generated.append(Path(temp_path).with_suffix(".svg"))

    base_svg = generated[0].read_text(encoding="utf-8")

    additional_paths = []

    for index, svg_path in enumerate(generated[1:], start=1):
        svg_text = svg_path.read_text(encoding="utf-8")

        polylines = re.findall(
            r"<polyline\b[^>]*(?:/>|>.*?</polyline>)",
            svg_text,
            flags=re.DOTALL,
        )

        color = COLORS[index % len(COLORS)]

        for polyline in polylines:
            polyline = re.sub(
                r'stroke="[^"]*"',
                f'stroke="{color}"',
                polyline,
                count=1,
            )
            additional_paths.append(polyline)

    intersections = _intersection_points(expressions)

    intersection_markup = []

    width = 1000
    height = 650
    xmin, xmax = -10, 10
    ymin, ymax = -10, 10

    def sx(xv):
        return (xv - xmin) / (xmax - xmin) * width

    def sy(yv):
        return height - (yv - ymin) / (ymax - ymin) * height

    for xv, yv in intersections:
        px = sx(xv)
        py = sy(yv)

        intersection_markup.append(
            f'''
            <circle cx="{px:.2f}" cy="{py:.2f}"
                    r="7"
                    fill="#f59e0b"
                    stroke="black"
                    stroke-width="2"/>

            <text x="{px + 10:.2f}" y="{py - 10:.2f}"
                  font-size="15"
                  font-family="sans-serif">
                ({xv:.2f}, {yv:.2f})
            </text>
            '''
        )

    insertion = "\n".join(additional_paths)
    intersection_insertion = "\n".join(intersection_markup)

    marker = "</svg>"

    if marker not in base_svg:
        raise ValueError("تعذر تركيب SVG متعدد الدوال.")

    combined_svg = base_svg.replace(
        marker,
        f'''
        <g id="additional-functions">
            {insertion}
        </g>

        <g id="intersection-points">
            {intersection_insertion}
        </g>

        </svg>
        ''',
        1,
    )

    output_svg = IMAGE_DIR / filename
    output_svg.write_text(combined_svg, encoding="utf-8")

    output_png = output_svg.with_suffix(".png")

    import cairosvg

    cairosvg.svg2png(
        bytestring=combined_svg.encode("utf-8"),
        write_to=str(output_png),
        output_width=width,
        output_height=height,
    )

    for temp in generated:
        try:
            temp.unlink()
        except OSError:
            pass

    return str(output_png)
