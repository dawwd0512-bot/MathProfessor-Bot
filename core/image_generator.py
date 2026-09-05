from pathlib import Path
import math
import sympy as sp
import cairosvg
from core.graph_analyzer import analyze_function

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = BASE_DIR / "data" / "generated_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _split_graph_expressions(expression):
    """Split one graph request into one or more expressions."""
    if isinstance(expression, (list, tuple)):
        return [str(item).strip() for item in expression if str(item).strip()]

    raw = str(expression).strip()
    raw = raw.replace("،", ",")

    parts = []
    for item in raw.replace(" و ", ",").split(","):
        item = item.strip()
        if item:
            parts.append(item)

    return parts or [raw]


def generate_function_graph(expression, filename="function.svg"):
    x = sp.Symbol("x")

    expressions = _split_graph_expressions(expression)

    # Step 4-A currently keeps the original single-expression behavior
    # while accepting a list/string containing multiple expressions.
    expr = sp.sympify(
        expressions[0],
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

    # ------------------------------------------------------------
    # Mathematical analysis
    # ------------------------------------------------------------
    analysis = analyze_function(expr)

    roots = analysis.get("roots", [])
    y_intercept = analysis.get("y_intercept")
    critical_points = analysis.get("critical_points", [])
    asymptotes = analysis.get("asymptotes", {})

    width = 1000
    height = 650

    xmin, xmax = -10, 10
    ymin, ymax = -10, 10

    def sx(xv):
        return (xv - xmin) / (xmax - xmin) * width

    def sy(yv):
        return height - (yv - ymin) / (ymax - ymin) * height

    # ------------------------------------------------------------
    # Generate graph segments.
    # Break the line when the function becomes undefined or jumps
    # sharply. This prevents false lines through asymptotes.
    # ------------------------------------------------------------
    segments = []
    current = []

    previous_y = None

    samples = 2001

    for i in range(samples):
        xv = xmin + (xmax - xmin) * i / (samples - 1)

        try:
            yv = float(fn(xv))

            if not math.isfinite(yv):
                raise ValueError

            if abs(yv) > ymax:
                raise ValueError

            if previous_y is not None:
                jump = abs(yv - previous_y)

                if jump > 3:
                    if current:
                        segments.append(current)
                    current = []

            px = sx(xv)
            py = sy(yv)

            current.append(f"{px:.2f},{py:.2f}")
            previous_y = yv

        except Exception:
            if current:
                segments.append(current)
            current = []
            previous_y = None

    if current:
        segments.append(current)

    if not segments:
        raise ValueError("تعذر إنشاء نقاط للرسم البياني.")

    # ------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------
    grid = []

    for value in range(math.ceil(xmin), math.floor(xmax) + 1):
        px = sx(value)
        grid.append(
            f'<line x1="{px:.2f}" y1="0" '
            f'x2="{px:.2f}" y2="{height}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )

    for value in range(math.ceil(ymin), math.floor(ymax) + 1):
        py = sy(value)
        grid.append(
            f'<line x1="0" y1="{py:.2f}" '
            f'x2="{width}" y2="{py:.2f}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
        )

    # ------------------------------------------------------------
    # Axes
    # ------------------------------------------------------------
    axis_x = sy(0)
    axis_y = sx(0)

    axes = f'''
    <line x1="0" y1="{axis_x:.2f}"
          x2="{width}" y2="{axis_x:.2f}"
          stroke="black" stroke-width="2"/>

    <line x1="{axis_y:.2f}" y1="0"
          x2="{axis_y:.2f}" y2="{height}"
          stroke="black" stroke-width="2"/>

    <polygon points="{width-12},{axis_x-6} {width-12},{axis_x+6} {width},{axis_x}"
             fill="black"/>

    <polygon points="{axis_y-6},12 {axis_y+6},12 {axis_y},0"
             fill="black"/>
    '''

    # ------------------------------------------------------------
    # Tick labels
    # ------------------------------------------------------------
    labels = []

    for value in range(math.ceil(xmin), math.floor(xmax) + 1):
        if value == 0:
            continue

        px = sx(value)

        labels.append(
            f'<text x="{px:.2f}" y="{axis_x + 22:.2f}" '
            f'font-size="14" text-anchor="middle">{value}</text>'
        )

    for value in range(math.ceil(ymin), math.floor(ymax) + 1):
        if value == 0:
            continue

        py = sy(value)

        labels.append(
            f'<text x="{axis_y - 10:.2f}" y="{py + 5:.2f}" '
            f'font-size="14" text-anchor="end">{value}</text>'
        )

    # ------------------------------------------------------------
    # Important mathematical points
    # ------------------------------------------------------------
    annotations = []

    def add_point(xv, yv, label):
        try:
            px = sx(float(xv))
            py = sy(float(yv))

            # Keep annotations inside the visible graph.
            if not (0 <= px <= width and 0 <= py <= height):
                return

            annotations.append(
                f'''
                <circle cx="{px:.2f}" cy="{py:.2f}"
                        r="6"
                        fill="#dc2626"
                        stroke="white"
                        stroke-width="2"/>

                <text x="{px + 9:.2f}" y="{py - 9:.2f}"
                      font-size="14"
                      font-family="sans-serif">
                    {label}
                </text>
                '''
            )
        except Exception:
            pass

    # x-intercepts
    for root in roots:
        if abs(root) <= 10:
            add_point(
                root,
                0,
                f"({root:.2f}, 0)"
            )

    # y-intercept
    if y_intercept is not None and abs(y_intercept) <= 10:
        add_point(
            0,
            y_intercept,
            f"(0, {y_intercept:.2f})"
        )

    # Critical points
    for point in critical_points:
        xv = point.get("x")
        yv = point.get("y")

        if (
            xv is not None
            and yv is not None
            and abs(xv) <= 10
            and abs(yv) <= 10
        ):
            add_point(
                xv,
                yv,
                f"({xv:.2f}, {yv:.2f})"
            )

    # ------------------------------------------------------------
    # Asymptotes
    # ------------------------------------------------------------
    asymptote_lines = []

    for value in asymptotes.get("vertical", []):
        if xmin <= value <= xmax:
            px = sx(value)

            asymptote_lines.append(
                f'''
                <line x1="{px:.2f}" y1="0"
                      x2="{px:.2f}" y2="{height}"
                      stroke="#dc2626"
                      stroke-width="2"
                      stroke-dasharray="8,7"
                      opacity="0.75"/>

                <text x="{px + 8:.2f}" y="30"
                      font-size="14"
                      font-family="sans-serif">
                    x = {value:.2f}
                </text>
                '''
            )

    for item in asymptotes.get("horizontal", []):
        value = item.get("y")

        if value is not None and ymin <= value <= ymax:
            py = sy(value)

            asymptote_lines.append(
                f'''
                <line x1="0" y1="{py:.2f}"
                      x2="{width}" y2="{py:.2f}"
                      stroke="#dc2626"
                      stroke-width="2"
                      stroke-dasharray="8,7"
                      opacity="0.75"/>

                <text x="{width - 12:.2f}" y="{py - 8:.2f}"
                      font-size="14"
                      font-family="sans-serif"
                      text-anchor="end">
                    y = {value:.2f}
                </text>
                '''
            )

    # ------------------------------------------------------------
    # Graph paths
    # ------------------------------------------------------------
    graph_paths = []

    for segment in segments:
        if len(segment) >= 2:
            graph_paths.append(
                f'''
                <polyline
                    points="{' '.join(segment)}"
                    fill="none"
                    stroke="#2563eb"
                    stroke-width="3"
                    stroke-linejoin="round"
                    stroke-linecap="round"/>
                '''
            )

    # ------------------------------------------------------------
    # SVG
    # ------------------------------------------------------------
    latex_expr = sp.latex(expr)

    svg = f'''
    <svg xmlns="http://www.w3.org/2000/svg"
         width="{width}" height="{height}"
         viewBox="0 0 {width} {height}">

        <rect width="100%" height="100%" fill="white"/>

        <g>
            {"".join(grid)}
        </g>

        <g>
            {axes}
        </g>

        <g>
            {"".join(labels)}
        </g>

        <g>
            {"".join(asymptote_lines)}
        </g>

        <g>
            {"".join(graph_paths)}
        </g>

        <g>
            {"".join(annotations)}
        </g>

        <rect x="18" y="18"
              width="300" height="42"
              rx="8"
              fill="white"
              stroke="#d1d5db"/>

        <text x="30" y="46"
              font-size="20"
              font-family="sans-serif">
            y = {latex_expr}
        </text>

        <text x="{width - 22}"
              y="{axis_x - 10:.2f}"
              font-size="18"
              font-family="sans-serif"
              text-anchor="end">
            x
        </text>

        <text x="{axis_y + 12:.2f}"
              y="22"
              font-size="18"
              font-family="sans-serif">
            y
        </text>

    </svg>
    '''

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
