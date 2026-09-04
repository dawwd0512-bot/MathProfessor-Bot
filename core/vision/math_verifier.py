from __future__ import annotations

import re

from core.ai.math_engine import solve_math


def verify_expression(expression: str) -> dict:
    """
    يحاول التحقق من تعبير رياضي باستخدام Math Engine.
    لا يعتبر الفشل في التحليل دليلًا على أن إجابة الصورة خاطئة.
    """

    expression = (expression or "").strip()

    if not expression:
        return {
            "verified": False,
            "status": "empty",
            "expression": expression,
        }

    try:
        result = solve_math(expression)

        return {
            "verified": True,
            "status": "ok",
            "expression": expression,
            "result": result,
        }

    except Exception as e:
        return {
            "verified": False,
            "status": "unavailable",
            "expression": expression,
            "error": str(e),
        }


def extract_simple_expressions(text: str) -> list[str]:
    """
    استخراج بسيط للتعبيرات التي تحتوي على مساواة.
    لا يحاول إعادة بناء الأسئلة المعقدة.
    """

    if not text:
        return []

    expressions = []

    for line in text.splitlines():
        line = line.strip()

        if "=" not in line:
            continue

        if len(line) > 200:
            continue

        if re.search(r"\d", line):
            expressions.append(line)

    return expressions


def verify_text(text: str) -> list[dict]:
    """
    يتحقق من التعبيرات البسيطة الموجودة في النص.
    """

    results = []

    for expression in extract_simple_expressions(text):
        results.append(
            verify_expression(expression)
        )

    return results
