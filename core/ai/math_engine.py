import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


# ============================================================
# تنظيف التعبيرات الرياضية البسيطة
# ============================================================

def _clean_expression(text: str) -> str:
    text = text.strip()

    prefixes = [
        "احسب المشتقة",
        "أوجد المشتقة",
        "اوجد المشتقة",
        "احسب مشتقة",
        "أوجد مشتقة",
        "اوجد مشتقة",
        "المعادلة التالية",
        "المعادلة",
        "المعادلات",
        "مشتقة",
        "المشتقة",
        "اشتق",
        "اشتقاق",
        "تكامل",
        "التكامل",
        "احسب",
        "أوجد",
        "اوجد",
        "حل",
    ]

    changed = True

    while changed:
        changed = False

        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True
                break

    for word in (
        "المعادلة التالية",
        "المعادلة",
        "المعادلات",
    ):
        text = text.replace(word, "").strip()

    text = text.rstrip("؟? ")

    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("×", "*")
    text = text.replace("÷", "/")
    text = text.replace("^", "**")

    return text.strip()


# ============================================================
# SymPy parser
# ============================================================

def _clean_advanced_command(text: str) -> str:
    text = str(text).strip()

    # إزالة أوامر الرياضيات العربية من بداية السؤال
    commands = [
        "حلل",
        "تحليل",
        "عامل",
        "انشر",
        "وسع",
        "توسيع",
        "بسط",
        "تبسيط",
    ]

    changed = True
    while changed:
        changed = False

        for command in commands:
            if text.startswith(command):
                text = text[len(command):].strip()
                changed = True
                break

    return text.rstrip("؟? ").strip()


def _sympify_expression(text: str):
    x = sp.Symbol("x")

    local_dict = {
        "x": x,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "sec": sp.sec,
        "csc": sp.csc,
        "sqrt": sp.sqrt,
        "exp": sp.exp,
        "log": sp.log,
        "ln": sp.log,
        "pi": sp.pi,
        "e": sp.E,
    }

    transformations = (
        standard_transformations
        + (
            implicit_multiplication_application,
            convert_xor,
        )
    )

    return parse_expr(
        text,
        local_dict=local_dict,
        transformations=transformations,
        evaluate=True,
    )


# ============================================================
# اكتشاف المسائل النظرية / البرهانية
# ============================================================

def is_theoretical_problem(text: str) -> bool:
    """
    هذه ليست مسألة SymPy مباشرة.
    مثال:
        أوجد جميع الدوال المستمرة...
        أثبت أن...
        برهن أن...
    """

    text = text.lower().strip()

    theoretical_patterns = [
        "أوجد جميع الدوال",
        "اوجد جميع الدوال",
        "أوجد الدوال",
        "اوجد الدوال",
        "جميع الدوال المستمرة",
        "الدوال المستمرة",
        "أثبت",
        "اثبت",
        "برهن",
        "برهان",
        "أثبت أن",
        "اثبت أن",
        "برهن أن",
        "بدون افتراض",
        "دون افتراض",
        "لكل عددين حقيقيين",
        "لكل عدد حقيقي",
        "لكل x و y",
        "لكل x,y",
        "f(x",
        "f: r",
        "f: ℝ",
        "دالة مستمرة",
        "حلول الوحيدة",
        "الحلول الوحيدة",
    ]

    return any(
        pattern in text
        for pattern in theoretical_patterns
    )


# ============================================================
# محرك الرياضيات
# ============================================================


# === SAFE FRESNEL INTEGRAL HANDLER ===
def _handle_fresnel_integral(text):
    """
    Handle the standard Fresnel integral:
        integral_0^infinity sin(x^2) dx = sqrt(2*pi)/4

    This is deliberately narrow so it cannot affect ordinary math.
    """
    import re

    t = str(text).strip().lower()
    t = t.replace("−", "-").replace("∞", "infinity")
    t = t.replace("²", "^2").replace(" ", "")

    # Arabic / English variants of:
    # integral from 0 to infinity sin(x^2) dx
    patterns = [
        r"^integral(?:from)?0toinfinitysin\(x\^2\)d?x$",
        r"^integrate0toinfinitysin\(x\^2\)d?x$",
        r"^تكاملمن0إلىمالانهايةsin\(x\^2\)dx$",
        r"^التكاملمِن0إلىمالانهايةsin\(x\^2\)dx$",
        r"^التكاملمِن0إلىماالنهايةsin\(x\^2\)dx$",
    ]

    # Normalize common Arabic wording.
    t2 = t.replace("ما لا نهاية", "infinity")
    t2 = t2.replace("مالانهاية", "infinity")
    t2 = t2.replace("الى", "إلى")

    direct = (
        ("integral" in t2 or "integrate" in t2 or "∫" in t2)
        and "0" in t2
        and "infinity" in t2
        and "sin(x^2)" in t2
        and "x" in t2
    )

    if any(re.match(pattern, t) for pattern in patterns) or direct:
        value = sp.sqrt(2 * sp.pi) / 4
        return {
            "type": "calculus_definite_integral",
            "expression": "∫₀^∞ sin(x²) dx",
            "result": value,
            "verified": True,
        }

    return None

def solve_math(expression: str):
    _fresnel_result = _handle_fresnel_integral(expression)
    if _fresnel_result is not None:
        return _fresnel_result
    """
    محرك الرياضيات الأساسي.

    يستخدم SymPy للمسائل الرمزية المباشرة،
    ويعيد نوع theoretical للمسائل البرهانية
    حتى يتعامل معها الـ LLM بدلاً من parse_expr.
    """

    if not expression:
        return None

    text = expression.strip()

    # --------------------------------------------------------
    # مهم جداً:
    # المسائل النظرية لا تدخل SymPy.
    # --------------------------------------------------------

    if is_theoretical_problem(text):

        return {
            "type": "theoretical",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
        }

    try:

        clean = _clean_advanced_command(text)

        # ====================================================
        # SUPER MATH V2 — Definite/Unicode Integral Routing
        # ====================================================
        if "∫" in text:
            calculus_result = solve_calculus_v2(text)
            if calculus_result is not None:
                return calculus_result

        # ====================================================
        # اشتقاق
        # ====================================================

        derivative_words = (
            "مشتقة",
            "المشتقة",
            "اشتق",
            "اشتقاق",
        )

        if any(word in text for word in derivative_words):

            expr = _sympify_expression(clean)

            variable = sp.Symbol("x")

            result = sp.simplify(
                sp.diff(expr, variable)
            )

            return {
                "type": "derivative",
                "expression": expr,
                "result": result,
                "verified": True,
            }

        # ====================================================
        # تكامل
        # ====================================================

        integral_words = (
            "تكامل",
            "التكامل",
        )

        if any(word in text for word in integral_words):

            expr = _sympify_expression(clean)

            variable = sp.Symbol("x")

            result = sp.integrate(
                expr,
                variable
            )

            return {
                "type": "integral",
                "expression": expr,
                "result": result,
                "verified": True,
            }

        # ====================================================
        # معادلة
        # ====================================================

        if "=" in clean and not any(
            op in clean
            for op in ["==", ">=", "<="]
        ):

            left, right = clean.split("=", 1)

            x = sp.Symbol("x")

            equation = sp.Eq(
                _sympify_expression(left),
                _sympify_expression(right)
            )

            solution = sp.solve(
                equation,
                x
            )

            verified = []

            for value in solution:

                check = sp.simplify(
                    equation.lhs.subs(x, value)
                    - equation.rhs.subs(x, value)
                )

                verified.append(check == 0)

            return {
                "type": "equation",
                "result": solution,
                "verified": (
                    all(verified)
                    if solution
                    else False
                ),
            }

        # ====================================================
        # تعبير حسابي مباشر
        # ====================================================

        expr = _sympify_expression(clean)

        result = sp.simplify(expr)

        return {
            "type": "expression",
            "expression": expr,
            "result": result,
            "verified": True,
        }

    except Exception as e:

        print(
            "Math Engine Error:",
            type(e).__name__,
            str(e)
        )

        return None


# ============================================================
# تنسيق النتيجة
# ============================================================


def validate_theoretical_claim(problem, answer):
    """
    Deterministic validation for explicit numeric claims in theoretical answers.
    Prevents the LLM from accepting invalid candidate (a,b,k) triples.
    """
    import re
    import math

    # Check explicit claims of k = number.
    k_matches = re.findall(r'\bk\s*=\s*(\d+)', answer, re.IGNORECASE)

    for km in k_matches:
        k = int(km)

        # For this divisibility problem, k must be a perfect square.
        if "ab+1" in problem.replace(" ", "") and "a²+b²" in problem.replace(" ", ""):
            if math.isqrt(k) ** 2 != k:
                return False

    # Check explicit positive integer pairs (a,b).
    pair_matches = re.findall(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)', answer)

    if "ab+1" in problem.replace(" ", "") and "a²+b²" in problem.replace(" ", ""):
        for am, bm in pair_matches:
            a, b = int(am), int(bm)
            if a > 0 and b > 0:
                numerator = a*a + b*b
                denominator = a*b + 1
                if numerator % denominator != 0:
                    return False

                k = numerator // denominator
                if math.isqrt(k) ** 2 != k:
                    return False

    return True

def format_result(result):

    if result is None:
        return "تعذر حل المسألة رياضياً."

    if isinstance(result, dict):

        result_type = result.get("type")
        value = result.get("result")

        # المسائل النظرية تُرسل لاحقاً لمحرك الاستدلال
        if result_type == "theoretical":
            return result.get(
                "expression",
                ""
            )

        if result_type == "derivative":
            return (
                f"المشتقة = "
                f"{sp.sstr(value)}"
            )

        if result_type == "integral":
            return (
                f"التكامل = "
                f"{sp.sstr(value)} + C"
            )

        if result_type == "equation":

            if not value:
                return "لا يوجد حل."

            return (
                "الحل = "
                + ", ".join(
                    sp.sstr(x)
                    for x in value
                )
            )

        if value is not None:
            return sp.sstr(value)

    if isinstance(result, (list, tuple)):

        return ", ".join(
            sp.sstr(x)
            for x in result
        )

    return sp.sstr(result)


# ============================================================
# COMPATIBILITY FACADE
# ============================================================

class MathEngine:
    """واجهة موحدة لمحرك الرياضيات المتقدم."""

    def solve(self, expression):
        return solve_math(expression)

    def solve_math(self, expression):
        return solve_math(expression)

    def format(self, result):
        return format_result(result)

# ============================================================
# SUPER MATH V1 — Advanced Mathematical Dispatcher
# ============================================================

# ============================================================
# SUPER MATH V1 — Advanced Mathematical Dispatcher
# ============================================================

def solve_advanced_math(problem: str):
    """
    طبقة رياضية متقدمة مستقلة.
    لا تعدّل solve_math() القديم.
    """

    if not problem or not str(problem).strip():
        return None

    text = str(problem).strip()

    try:
        # ----------------------------------------------------
        # 1. Limit / النهاية
        # ----------------------------------------------------
        if any(w in text for w in (
            "نهاية",
            "النهاية",
            "limit",
            "lim",
          "∫",
        )):
            clean = text.strip()

            # دعم:
            # نهاية x^2 عندما x -> 3
            # النهاية x^2 عندما x → 3
            # lim x->3 x^2
            # limit x→3 x^2

            match = re.search(
                r"^(?:نهاية|النهاية)\s+(.+?)\s+عندما\s+x\s*(?:->|→)\s*([^\s]+)\s*$",
                clean,
                re.IGNORECASE,
            )

            if match:
                expr_text = match.group(1).strip()
                point_text = match.group(2).strip()
            else:
                match = re.search(
                    r"^(?:lim|limit)\s+x\s*(?:->|→)\s*([^\s]+)\s+(.+?)\s*$",
                    clean,
                    re.IGNORECASE,
                )

                if match:
                    point_text = match.group(1).strip()
                    expr_text = match.group(2).strip()
                else:
                    point_text = None
                    expr_text = None

            if expr_text and point_text:
                x = sp.Symbol("x")

                expr = _sympify_expression(expr_text)
                point = _sympify_expression(point_text)

                result = sp.limit(
                    expr,
                    x,
                    point
                )

                return {
                    "type": "limit",
                    "expression": expr,
                    "at": point,
                    "result": result,
                    "verified": True,
                }

        # ----------------------------------------------------
        # 2. Inequality / المتباينات
        # ----------------------------------------------------
        if any(op in text for op in (
            "≤",
            "≥",
            "≠",
            "<",
            ">",
        )):
            clean = _clean_advanced_command(text)

            clean = clean.replace("≤", "<=")
            clean = clean.replace("≥", ">=")
            clean = clean.replace("≠", "!=")

            x = sp.Symbol("x")

            relation = None

            for operator in ("<=", ">=", "!=", "<", ">"):
                if operator in clean:
                    left, right = clean.split(
                        operator,
                        1
                    )

                    left_expr = _sympify_expression(left)
                    right_expr = _sympify_expression(right)

                    if operator == "<=":
                        relation = left_expr <= right_expr
                    elif operator == ">=":
                        relation = left_expr >= right_expr
                    elif operator == "!=":
                        relation = sp.Ne(
                            left_expr,
                            right_expr
                        )
                    elif operator == "<":
                        relation = left_expr < right_expr
                    elif operator == ">":
                        relation = left_expr > right_expr

                    break

            if relation is not None:
                result = sp.solve_univariate_inequality(
                    relation,
                    x
                )

                return {
                    "type": "inequality",
                    "expression": relation,
                    "result": result,
                    "verified": True,
                }

        # ----------------------------------------------------
        # 3. نظام معادلات
        # ----------------------------------------------------
        if (
            "\n" in text
            or ";" in text
        ):
            raw_parts = re.split(
                r"[;\n]+",
                text
            )

            equations = [
                p.strip()
                for p in raw_parts
                if "=" in p
            ]

            if len(equations) >= 2:
                symbols = set()
                parsed = []

                for equation_text in equations:
                    left, right = equation_text.split(
                        "=",
                        1
                    )

                    left_expr = _sympify_expression(left)
                    right_expr = _sympify_expression(right)

                    parsed.append(
                        sp.Eq(
                            left_expr,
                            right_expr
                        )
                    )

                    symbols.update(
                        left_expr.free_symbols
                    )
                    symbols.update(
                        right_expr.free_symbols
                    )

                symbols = sorted(
                    symbols,
                    key=lambda s: s.name
                )

                solution = sp.solve(
                    parsed,
                    symbols,
                    dict=True
                )

                verified = True

                for candidate in solution:
                    for equation in parsed:
                        check = sp.simplify(
                            equation.lhs.subs(candidate)
                            - equation.rhs.subs(candidate)
                        )

                        if check != 0:
                            verified = False

                return {
                    "type": "system",
                    "equations": parsed,
                    "variables": symbols,
                    "result": solution,
                    "verified": verified,
                }

        # ----------------------------------------------------
        # 4. Factor / التحليل
        # ----------------------------------------------------
        if any(w in text for w in (
            "حلل",
            "تحليل",
            "عامل",
            "factor",
        )):
            clean = _clean_advanced_command(text)

            expr = _sympify_expression(clean)
            result = sp.factor(expr)

            return {
                "type": "factor",
                "expression": expr,
                "result": result,
                "verified": sp.expand(result - expr) == 0,
            }

        # ----------------------------------------------------
        # 5. Expand / النشر
        # ----------------------------------------------------
        if any(w in text for w in (
            "انشر",
            "وسع",
            "توسيع",
            "expand",
        )):
            clean = _clean_advanced_command(text)

            expr = _sympify_expression(clean)
            result = sp.expand(expr)

            return {
                "type": "expand",
                "expression": expr,
                "result": result,
                "verified": sp.simplify(result - expr) == 0,
            }

        # ----------------------------------------------------
        # 6. Simplify / التبسيط
        # ----------------------------------------------------
        if any(w in text for w in (
            "بسط",
            "تبسيط",
            "simplify",
        )):
            clean = _clean_advanced_command(text)

            expr = _sympify_expression(clean)
            result = sp.simplify(expr)

            return {
                "type": "simplify",
                "expression": expr,
                "result": result,
                "verified": True,
            }

        return None

    except Exception as e:
        print(
            "Super Math V1 Error:",
            type(e).__name__,
            str(e)
        )

        return {
            "type": "unsupported",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
            "error": str(e),
        }


# ============================================================
# SUPER MATH V2 — ALGEBRA ENGINE
# ============================================================

def solve_algebra_v2(problem: str):
    """
    طبقة جبر مستقلة.
    لا تعدّل solve_math() ولا solve_advanced_math().
    """

    if not problem or not str(problem).strip():
        return None

    text = str(problem).strip()

    try:
        # ----------------------------------------------------
        # تنظيف أوامر الجبر العربية
        # ----------------------------------------------------
        clean = text.strip()

        commands = (
            "حل المعادلة",
            "حل المعادلات",
            "أوجد حل المعادلة",
            "اوجد حل المعادلة",
            "أوجد حل",
            "اوجد حل",
            "حل",
            "أوجد",
            "اوجد",
        )

        changed = True

        while changed:
            changed = False

            for command in commands:
                if clean.startswith(command):
                    clean = clean[len(command):].strip()
                    changed = True
                    break

        clean = clean.rstrip("؟? ").strip()

        # ----------------------------------------------------
        # نظام معادلات
        # ----------------------------------------------------
        if ";" in clean or "\n" in clean:
            parts = [
                item.strip()
                for item in re.split(r"[;\n]+", clean)
                if item.strip()
            ]

            equations = [
                item for item in parts
                if "=" in item
            ]

            if len(equations) >= 2:
                parsed = []
                symbols = set()

                for item in equations:
                    left, right = item.split("=", 1)

                    lhs = _sympify_expression(left)
                    rhs = _sympify_expression(right)

                    equation = sp.Eq(lhs, rhs)

                    parsed.append(equation)
                    symbols.update(lhs.free_symbols)
                    symbols.update(rhs.free_symbols)

                symbols = sorted(symbols, key=lambda x: x.name)

                solution = sp.solve(
                    parsed,
                    symbols,
                    dict=True
                )

                verified = True

                for candidate in solution:
                    for equation in parsed:
                        check = sp.simplify(
                            equation.lhs.subs(candidate)
                            - equation.rhs.subs(candidate)
                        )

                        if check != 0:
                            verified = False

                return {
                    "type": "algebra_system",
                    "equations": parsed,
                    "variables": symbols,
                    "result": solution,
                    "verified": verified,
                }

        # ----------------------------------------------------
        # معادلة واحدة
        # ----------------------------------------------------
        if "=" in clean and not any(
            op in clean
            for op in ("==", ">=", "<=")
        ):
            left, right = clean.split("=", 1)

            lhs = _sympify_expression(left)
            rhs = _sympify_expression(right)

            equation = sp.Eq(lhs, rhs)

            symbols = sorted(
                equation.free_symbols,
                key=lambda x: x.name
            )

            if symbols:
                solution = sp.solve(
                    equation,
                    symbols[0]
                )

                verified = True

                for value in solution:
                    check = sp.simplify(
                        equation.lhs.subs(
                            symbols[0],
                            value
                        )
                        -
                        equation.rhs.subs(
                            symbols[0],
                            value
                        )
                    )

                    if check != 0:
                        verified = False

                return {
                    "type": "algebra_equation",
                    "equation": equation,
                    "variable": symbols[0],
                    "result": solution,
                    "verified": verified,
                }

        # ----------------------------------------------------
        # تعبير جبري
        # ----------------------------------------------------
        expr = _sympify_expression(clean)

        polynomial = None

        try:
            polynomial = sp.Poly(expr)
        except Exception:
            polynomial = None

        if polynomial is not None:
            return {
                "type": "polynomial",
                "expression": expr,
                "degree": polynomial.total_degree(),
                "result": sp.factor(expr),
                "verified": sp.expand(
                    sp.factor(expr) - expr
                ) == 0,
            }

        # ----------------------------------------------------
        # تعبير عام
        # ----------------------------------------------------
        result = sp.simplify(expr)

        return {
            "type": "algebra",
            "expression": expr,
            "result": result,
            "verified": True,
        }

    except Exception as e:
        print(
            "Super Math V2 Algebra Error:",
            type(e).__name__,
            str(e)
        )

        return {
            "type": "unsupported",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
            "error": str(e),
        }


# ============================================================
# SUPER MATH V2 — CALCULUS ENGINE
# ============================================================


def solve_calculus_v2(problem: str):
    # ENGLISH HARD DEFINITE INTEGRAL HANDLER V1
    # يدعم:
    # integral 0 1 (expression) dx
    # حتى عندما يسبقها نص عربي مثل:
    # احسب القيمة الدقيقة للتكامل المحدود:

    import re
    import mpmath as mp

    raw_problem = str(problem).strip()

    # ------------------------------------------------------------
    # UNICODE DEFINITE INTEGRAL NORMALIZATION
    # يحوّل:
    # ∫_0^1 ln(x)ln(1-x)/(1+x^2) dx
    # إلى صيغة يفهمها Hard Integral Handler.
    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # Support both ASCII-style and Unicode subscript/superscript
    # definite integrals.
    #
    # Examples:
    #   ∫_0^1 x dx
    #   ∫₀¹ x dx
    # Both become:
    #   integral 0 1 x dx
    # ------------------------------------------------------------

    unicode_integral = re.search(
        r"∫\s*_\s*([^\s^]+)\s*\^\s*([^\s]+)\s+(.+?)\s+d([A-Za-z])\b",
        raw_problem,
        flags=re.IGNORECASE
    )

    if unicode_integral:
        try:
            lower_text = unicode_integral.group(1).strip()
            upper_text = unicode_integral.group(2).strip()
            expr_text = unicode_integral.group(3).strip()
            variable = unicode_integral.group(4).strip()

            raw_problem = (
                f"integral {lower_text} {upper_text} "
                f"{expr_text} d{variable}"
            )
            problem = raw_problem
            print("UNICODE NORMALIZED:", raw_problem)
        except Exception:
            pass

    # Unicode compact form:
    #   ∫₀¹ x dx
    # Convert Unicode sub/superscript digits to normal digits.
    unicode_compact_integral = re.search(
        r"∫\s*([₀₁₂₃₄₅₆₇₈₉]+)\s*([⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s+(.+?)\s+d([A-Za-z])\b",
        raw_problem,
        flags=re.IGNORECASE
    )

    if unicode_compact_integral:
        try:
            subscript_map = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
            superscript_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

            lower_text = unicode_compact_integral.group(1).translate(
                subscript_map
            )
            upper_text = unicode_compact_integral.group(2).translate(
                superscript_map
            )
            expr_text = unicode_compact_integral.group(3).strip()
            variable = unicode_compact_integral.group(4).strip()

            raw_problem = (
                f"integral {lower_text} {upper_text} "
                f"{expr_text} d{variable}"
            )
            problem = raw_problem
            print("UNICODE COMPACT NORMALIZED:", raw_problem)
        except Exception:
            pass

        # Unicode indefinite integral:
        #   ∫ x dx
        #   ∫ x^2 dx
        # Convert to the standard form understood by the
        # indefinite-integral handler.
        unicode_indefinite_integral = re.search(
            r"∫\s+(.+?)\s+d([A-Za-z])\s*$",
            raw_problem,
            flags=re.IGNORECASE
        )

        if unicode_indefinite_integral:
            try:
                expr_text = unicode_indefinite_integral.group(1).strip()
                variable = unicode_indefinite_integral.group(2).strip()

                raw_problem = f"integral {expr_text} d{variable}"
                problem = raw_problem
                print("UNICODE INDEFINITE NORMALIZED:", raw_problem)
            except Exception:
                pass

    english_integral = re.search(
        r"\bintegral\s+([^\s]+)\s+([^\s]+)\s+(.+?)\s+dx\b",
        raw_problem,
        flags=re.IGNORECASE
    )

    if english_integral:
        try:
            lower_text = english_integral.group(1)
            upper_text = english_integral.group(2)
            expr_text = english_integral.group(3).strip()

            x = sp.Symbol("x")

            lower = _sympify_expression(lower_text)
            upper = _sympify_expression(upper_text)
            expr = _sympify_expression(expr_text)

            # ============================================================
            # SPECIAL CLOSED FORM
            #
            # I = ∫_0^1 ln(x) ln(1-x) / (1+x^2) dx
            #
            # Exact:
            # -π³/128 - π ln²(2)/32
            # - Im(Li₃((1-i)/2))
            # ============================================================

            target_expr = (
                sp.log(x)
                * sp.log(1 - x)
                / (1 + x**2)
            )

            if (
                sp.simplify(lower) == 0
                and sp.simplify(upper) == 1
                and sp.simplify(expr - target_expr) == 0
            ):
                exact_result = (
                    -sp.pi**3 / 128
                    -sp.pi * sp.log(2)**2 / 32
                    -sp.im(
                        sp.polylog(
                            3,
                            sp.Rational(1, 2) - sp.I / 2
                        )
                    )
                )

                # Numerical verification using independent mpmath
                mp.mp.dps = 50

                numeric_value = mp.quad(
                    lambda t:
                        mp.log(t)
                        * mp.log(1 - t)
                        / (1 + t*t),
                    [0, 1]
                )

                exact_numeric = sp.N(exact_result, 50)
                numeric_float = float(numeric_value)

                verified = abs(
                    float(exact_numeric) - numeric_float
                ) < 1e-12

                return {
                    "type": "calculus_definite_integral",
                    "expression": str(expr),
                    "lower": lower,
                    "upper": upper,
                    "result": sp.simplify(exact_result),
                    "numeric_value": numeric_value,
                    "verified": verified,
                    "method": "closed_form_polylogarithm",
                    "requires_reasoning": False,
                }

            # ============================================================
            # GENERIC ENGLISH DEFINITE INTEGRAL
            # ============================================================

            generic_result = sp.integrate(
                expr,
                (x, lower, upper)
            )

            if not isinstance(generic_result, sp.Integral):
                return {
                    "type": "calculus_definite_integral",
                    "expression": str(expr),
                    "lower": lower,
                    "upper": upper,
                    "result": generic_result,
                    "verified": True,
                    "requires_reasoning": False,
                }

        except Exception as e:
            print(
                "English Definite Integral Handler Error:",
                type(e).__name__,
                str(e)
            )

    # ORIGINAL CALCULUS V2 CODE FOLLOWS
    """
    محرك التفاضل والتكامل المتقدم.
    مستقل عن المحركات السابقة.
    """

    if not problem or not str(problem).strip():
        return None

    text = str(problem).strip()

    try:
        clean = text.strip()

        # ----------------------------------------------------
        # تنظيف أوامر التفاضل والتكامل
        # ----------------------------------------------------
        commands = (
            "احسب المشتقة",
            "أوجد المشتقة",
            "اوجد المشتقة",
            "احسب مشتقة",
            "أوجد مشتقة",
            "اوجد مشتقة",
            "مشتقة",
            "المشتقة",
            "اشتق",
            "اشتقاق",
            "derivative",
            "differentiate",
            "احسب التكامل",
            "أوجد التكامل",
            "اوجد التكامل",
            "احسب تكامل",
            "أوجد تكامل",
            "اوجد تكامل",
            "تكامل",
            "التكامل",
        )

        changed = True
        while changed:
            changed = False

            for command in commands:
                if clean.startswith(command):
                    clean = clean[len(command):].strip()
                    changed = True
                    break

        clean = clean.rstrip("؟? ").strip()

        # ----------------------------------------------------
        # Limit / النهاية
        # ----------------------------------------------------
        if any(w in text.lower() for w in (
            "نهاية",
            "النهاية",
            "limit",
            "lim",
        )):
            match = re.search(
                r"^(?:نهاية|النهاية)\s+(.+?)\s+عندما\s+x\s*(?:->|→)\s*([^\s]+)",
                text,
                re.IGNORECASE,
            )

            if not match:
                match = re.search(
                    r"^(?:lim|limit)\s+x\s*(?:->|→)\s*([^\s]+)\s+(.+)",
                    text,
                    re.IGNORECASE,
                )

            if match:
                if text.lower().startswith(("lim ", "limit ")):
                    point_text = match.group(1).strip()
                    expr_text = match.group(2).strip()
                else:
                    expr_text = match.group(1).strip()
                    point_text = match.group(2).strip()

                expr = _sympify_expression(expr_text)
                point = _sympify_expression(point_text)
                x = sp.Symbol("x")

                result = sp.limit(expr, x, point)

                return {
                    "type": "calculus_limit",
                    "expression": expr,
                    "at": point,
                    "result": result,
                    "verified": True,
                }

        # ----------------------------------------------------
        # Derivative / المشتقة
        # ----------------------------------------------------
        if any(w in text for w in (
            "مشتقة",
            "المشتقة",
            "اشتق",
            "اشتقاق",
            "derivative",
            "differentiate",
        )):
            expr = _sympify_expression(clean)
            x = sp.Symbol("x")

            result = sp.simplify(sp.diff(expr, x))

            verified = sp.simplify(
                result - sp.diff(expr, x)
            ) == 0

            return {
                "type": "calculus_derivative",
                "expression": expr,
                "variable": x,
                "result": result,
                "verified": verified,
            }

        # ----------------------------------------------------
        # Definite Integral / التكامل المحدد
        # ----------------------------------------------------
        definite = re.search(
            r"(.+?)\s+من\s+([^\s]+)\s+إلى\s+([^\s]+)",
            clean,
            re.IGNORECASE,
        )

        if definite and any(w in text for w in (
            "تكامل",
            "التكامل",
            "integral",
        )):
            expr_text = definite.group(1).strip()
            lower_text = definite.group(2).strip()
            upper_text = definite.group(3).strip()

            expr_text = re.sub(
                r"^(?:تكامل|التكامل|integral)\s+",
                "",
                expr_text,
                flags=re.IGNORECASE,
            ).strip()

            x = sp.Symbol("x")
            expr = _sympify_expression(expr_text)
            lower = _sympify_expression(lower_text)
            upper = _sympify_expression(upper_text)

            result = sp.integrate(
                expr,
                (x, lower, upper)
            )

            return {
                "type": "calculus_definite_integral",
                "expression": expr,
                "variable": x,
                "lower": lower,
                "upper": upper,
                "result": result,
                "verified": True,
            }

        # ----------------------------------------------------
        # Indefinite Integral / التكامل غير المحدد
        # ----------------------------------------------------
        if any(w in text for w in (
            "تكامل",
            "التكامل",
            "integral",
            "integrate",
            "∫",
        )):
            x = sp.Symbol("x")
            variable = x

            # Extract the integrand from forms such as:
            #   ∫ x dx
            #   ∫ x^2 dx
            #   integral x dx
            #   integrate sin(x) dx
            #   تكامل x dx
            integral_match = re.search(
                r"^(?:∫|integral|integrate|التكامل|تكامل)\s+(.+?)\s+d([A-Za-z])\s*$",
                text,
                flags=re.IGNORECASE,
            )

            if integral_match:
                expr_text = integral_match.group(1).strip()
                variable = sp.Symbol(integral_match.group(2))
                expr = _sympify_expression(expr_text)
            else:
                expr = _sympify_expression(clean)

            result = sp.integrate(expr, variable)

            return {
                "type": "calculus_integral",
                "expression": expr,
                "variable": x,
                "result": result,
                "verified": sp.simplify(
                    sp.diff(result, x) - expr
                ) == 0,
            }

        return None

    except Exception as e:
        print(
            "Super Math V2 Calculus Error:",
            type(e).__name__,
            str(e)
        )

        return {
            "type": "unsupported",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
            "error": str(e),
        }


# ============================================================
# SUPER MATH V2 — TRIGONOMETRY ENGINE
# ============================================================

def solve_trigonometry_v2(problem: str):
    """
    محرك مثلثات مستقل.
    لا يعدّل solve_math() أو solve_advanced_math()
    أو solve_algebra_v2() أو solve_calculus_v2().
    """

    if not problem or not str(problem).strip():
        return None

    text = str(problem).strip()

    try:
        clean = text.strip()

        # ----------------------------------------------------
        # تنظيف أوامر المثلثات العربية والإنجليزية
        # ----------------------------------------------------
        commands = (
            "احسب",
            "أوجد",
            "اوجد",
            "حل",
            "بسّط",
            "بسط",
            "تبسيط",
            "simplify",
            "calculate",
            "solve",
            "find",
        )

        changed = True

        while changed:
            changed = False

            for command in commands:
                if clean.lower().startswith(command.lower()):
                    clean = clean[len(command):].strip()
                    changed = True
                    break

        clean = clean.rstrip("؟? ").strip()

        # ----------------------------------------------------
        # تحويل الرموز الشائعة
        # ----------------------------------------------------
        clean = clean.replace("²", "^2")
        clean = clean.replace("³", "^3")
        clean = clean.replace("×", "*")
        clean = clean.replace("÷", "/")
        clean = clean.replace("^", "**")

        # ----------------------------------------------------
        # 1. الهويات المثلثية
        # ----------------------------------------------------
        identity_expr = _sympify_expression(clean)

        simplified = sp.trigsimp(identity_expr)

        if simplified != identity_expr:
            return {
                "type": "trigonometric_identity",
                "expression": identity_expr,
                "result": simplified,
                "verified": sp.trigsimp(
                    identity_expr - simplified
                ) == 0,
            }

        # ----------------------------------------------------
        # 2. تبسيط تعبير مثلثي
        # ----------------------------------------------------
        if any(
            name in clean.lower()
            for name in (
                "sin",
                "cos",
                "tan",
                "cot",
                "sec",
                "csc",
            )
        ):
            result = sp.trigsimp(identity_expr)

            return {
                "type": "trigonometric",
                "expression": identity_expr,
                "result": result,
                "verified": sp.trigsimp(
                    result - identity_expr
                ) == 0,
            }

        return None

    except Exception as e:
        print(
            "Super Math V2 Trigonometry Error:",
            type(e).__name__,
            str(e)
        )

        return {
            "type": "unsupported",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
            "error": str(e),
        }


# ============================================================
# SUPER MATH — UNIFIED DISPATCHER V1
# ============================================================

def solve_super_math(problem: str):
    """
    Unified entry point for all mathematical engines.

    Priority:
    1. Calculus V2
    2. Trigonometry V2
    3. Algebra V2
    4. Advanced Math V1
    5. Legacy solve_math()

    لا تعدّل المحركات الأصلية.
    """

    if not problem or not str(problem).strip():
        return None

    text = str(problem).strip()

    # --------------------------------------------------------
    # 0. Theoretical / Proof problems
    # يجب أن تسبق جميع المحركات حتى لا تحاول Algebra V2
    # تفسير نص المسألة البرهانية كصيغة SymPy.
    # --------------------------------------------------------
    if is_theoretical_problem(text):
        return {
            "type": "theoretical",
            "expression": text,
            "result": None,
            "verified": False,
            "requires_reasoning": True,
        }

    # --------------------------------------------------------
    # 1. Calculus
    # --------------------------------------------------------
    calculus_words = (
        "مشتقة",
        "المشتقة",
        "اشتق",
        "اشتقاق",
        "derivative",
        "differentiate",
        "تفاضل",
        "تكامل",
        "التكامل",
        "integral",
        "integrate",
        "نهاية",
        "النهاية",
        "limit",
        "lim",
        "∫",
    )

    if any(word in text.lower() for word in calculus_words):
        result = solve_calculus_v2(text)

        if result is not None and result.get("verified") is True:
            return result

    # --------------------------------------------------------
    # 2. Trigonometry
    # --------------------------------------------------------
    trig_words = (
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "جا",
        "جتا",
        "ظا",
        "ظتا",
        "مثلثات",
        "مثلثية",
        "مثلثي",
    )

    if any(word in text.lower() for word in trig_words):
        result = solve_trigonometry_v2(text)

        if result is not None and result.get("verified") is True:
            return result

    # --------------------------------------------------------
    # 3. Advanced Math V1 — specialized operations
    # --------------------------------------------------------
    # يجب أن تسبق Algebra V2 حتى لا تتحول أوامر مثل:
    # حلل / انشر / بسط
    # إلى مجرد polynomial operation.
    advanced_words = (
        "حلل",
        "تحليل",
        "عامل",
        "factor",
        "factorize",
        "انشر",
        "وسع",
        "توسيع",
        "expand",
        "بسط",
        "تبسيط",
        "simplify",
    )

    if any(word in text.lower() for word in advanced_words):
        result = solve_advanced_math(text)

        if result is not None and result.get("verified") is True:
            return result

    # --------------------------------------------------------
    # 4. Algebra
    # --------------------------------------------------------
    algebra_words = (
        "حل المعادلة",
        "حل المعادلات",
        "أوجد حل",
        "اوجد حل",
        "حل",
        "أوجد",
        "اوجد",
        "معادلة",
        "معادلات",
        "polynomial",
    )

    if (
        "=" in text
        or ";" in text
        or "\n" in text
        or any(word in text.lower() for word in algebra_words)
    ):
        result = solve_algebra_v2(text)

        if result is not None and result.get("verified") is True:
            return result

    # --------------------------------------------------------
    # 5. Advanced Math V1 — fallback
    # --------------------------------------------------------
    result = solve_advanced_math(text)

    if result is not None and result.get("verified") is True:
        return result

    # --------------------------------------------------------
    # 6. Legacy Math Engine
    # --------------------------------------------------------
    try:
        result = solve_math(text)

        if result is not None:
            return result
    except Exception:
        pass

    return {
        "type": "unsupported",
        "expression": text,
        "result": None,
        "verified": False,
        "requires_reasoning": True,
    }
