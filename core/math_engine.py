import sympy as sp


def solve_equation(equation: str):
    x = sp.symbols("x")

    equation = equation.replace("^", "**")
    left, right = equation.split("=")

    expr = sp.sympify(left) - sp.sympify(right)

    return sp.solve(expr, x)


def derivative(expression: str):
    x = sp.symbols("x")

    expression = expression.replace("^", "**")

    return sp.diff(
        sp.sympify(expression),
        x
    )


def integral(expression: str):
    x = sp.symbols("x")

    expression = expression.replace("^", "**")

    return sp.integrate(
        sp.sympify(expression),
        x
    )


def simplify(expression: str):
    expression = expression.replace("^", "**")

    return sp.simplify(
        sp.sympify(expression)
    )


# ============================================================
# COMPATIBILITY FACADE
# ============================================================

class MathEngine:
    """واجهة موحدة للتوافق مع الأجزاء التي تستورد MathEngine."""

    def solve_equation(self, equation):
        return solve_equation(equation)

    def derivative(self, expression):
        return derivative(expression)

    def integral(self, expression):
        return integral(expression)

    def simplify(self, expression):
        return simplify(expression)
