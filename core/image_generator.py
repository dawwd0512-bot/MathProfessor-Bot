from pathlib import Path
import sympy as sp
import cairosvg

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "data" / "generated_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_function_graph(expression, filename="function.svg"):
    x = sp.Symbol("x")

    expr = sp.sympify(
        str(expression),
        locals={
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
    )

    fn = sp.lambdify(x, expr, "math")

    width = 900
    height = 500

    xmin, xmax = -10, 10
    ymin, ymax = -10, 10

    points = []

    for i in range(801):
        xv = xmin + (xmax - xmin) * i / 800

        try:
            yv = float(fn(xv))

            if not (ymin <= yv <= ymax):
                continue

            px = (xv - xmin) / (xmax - xmin) * width
            py = height - (yv - ymin) / (ymax - ymin) * height

            points.append(f"{px:.2f},{py:.2f}")

        except Exception:
            continue

    if not points:
        raise ValueError("تعذر إنشاء نقاط للرسم البياني.")

    path_data = " ".join(points)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{width}" height="{height}" viewBox="0 0 {width} {height}">

<rect width="100%" height="100%" fill="white"/>

<line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}"
stroke="black" stroke-width="2"/>

<line x1="{width/2}" y1="0" x2="{width/2}" y2="{height}"
stroke="black" stroke-width="2"/>

<polyline points="{path_data}"
fill="none"
stroke="blue"
stroke-width="3"/>

<text x="20" y="30" font-size="20">
y = {sp.latex(expr)}
</text>

<text x="{width-30}" y="{height/2-8}" font-size="16">x</text>
<text x="{width/2+8}" y="20" font-size="16">y</text>

</svg>'''

    # حفظ SVG داخليًا ثم تحويله مباشرة إلى PNG
    svg_output = IMAGE_DIR / filename
    svg_output.write_text(svg, encoding="utf-8")

    png_output = svg_output.with_suffix(".png")

    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=str(png_output),
        output_width=width,
        output_height=height,
    )

    return str(png_output)
