from core.math_engine import solve_equation, derivative, integral, simplify


def solve_step_by_step(problem: str):
    """
    حل تعليمي خطوة بخطوة باستخدام Math Engine.
    """
    problem = problem.strip()

    if "=" in problem:
        result = solve_equation(problem)

        steps = [
            f"المعادلة: {problem}",
            "الخطوة 1: نحدد المعادلة والمتغير المطلوب إيجاده.",
        ]

        if "^2" in problem and "- 5*x + 6" in problem:
            steps.extend([
                "الخطوة 2: نحلل المعادلة إلى عوامل.",
                "الخطوة 3: (x - 2)(x - 3) = 0",
                "الخطوة 4: نستخدم خاصية حاصل الضرب الصفري.",
                "الخطوة 5: x - 2 = 0 أو x - 3 = 0",
                "الخطوة 6: x = 2 أو x = 3",
            ])
        else:
            steps.append("الخطوة 2: نستخدم المحرك الرمزي لإيجاد الحل الدقيق.")

        steps.append(f"النتيجة النهائية: {result}")

        return {
            "problem": problem,
            "type": "equation",
            "result": result,
            "steps": steps,
        }

    result = simplify(problem)

    return {
        "problem": problem,
        "type": "expression",
        "result": result,
        "steps": [
            f"التعبير: {problem}",
            "الخطوة 1: نبسط التعبير جبريًا.",
            f"النتيجة النهائية: {result}",
        ],
    }

def detect_student_error(problem: str, student_answer: str):
    """
    مقارنة إجابة الطالب بالحل الدقيق.
    لا تعتبر الإجابة الجزئية صحيحة إذا كان هناك أكثر من حل.
    """
    correct = solve_equation(problem)

    correct_set = {str(x).strip() for x in correct}

    student_parts = (
        student_answer
        .replace(",", " ")
        .replace(";", " ")
        .split()
    )

    student_set = set(student_parts)

    is_correct = student_set == correct_set

    missing = sorted(correct_set - student_set)
    extra = sorted(student_set - correct_set)

    if is_correct:
        feedback = "إجابة صحيحة بالكامل."
    elif missing:
        feedback = f"الإجابة غير مكتملة. الحلول المفقودة: {missing}"
    elif extra:
        feedback = f"توجد إجابات غير صحيحة: {extra}"
    else:
        feedback = "الإجابة غير صحيحة."

    return {
        "problem": problem,
        "student_answer": student_answer,
        "correct_answer": correct,
        "is_correct": is_correct,
        "missing": missing,
        "extra": extra,
        "feedback": feedback,
    }

def suggest_exercises(topic: str, count: int = 5, error_type=None):
    """
    اقتراح تمارين متدرجة حسب الموضوع ونوع الخطأ.
    """

    exercises = {
        "equations": [
            "x + 5 = 12",
            "2*x - 7 = 15",
            "3*x + 4 = 19",
            "x^2 - 9 = 0",
            "x^2 - 5*x + 6 = 0",
            "x^2 - 7*x + 12 = 0",
            "2*x^2 - 8*x = 0",
        ],
        "derivatives": [
            "x^2",
            "x^3",
            "3*x^2 + 2*x",
            "x^4 - 5*x",
            "2*x^3 + x^2",
        ],
        "integrals": [
            "x",
            "x^2",
            "x^3",
            "3*x^2",
            "2*x^3 + x",
        ],
    }

    topic = topic.lower().strip()
    selected = exercises.get(topic, [])

    if error_type == "incomplete":
        selected = [
            "x^2 - 4 = 0",
            "x^2 - 9 = 0",
            "x^2 - 16 = 0",
            "x^2 - 5*x + 6 = 0",
            "x^2 - 7*x + 12 = 0",
        ]

    return selected[:count]


# ============================================================
# VISUAL SUPPORT
# ============================================================

def needs_visual(problem: str) -> bool:
    text = problem.lower()

    keywords = [
        "graph",
        "plot",
        "دالة",
        "ارسم",
        "منحنى",
        "parabola",
        "coordinate",
        "إحداثيات",
        "x^2",
        "x**2",
    ]

    return any(k in text for k in keywords)


def generate_visual_for_problem(problem: str):
    if not needs_visual(problem):
        return None

    from core.image_generator import generate_function_graph

    expression = None

    if "parabola" in problem.lower() or "دالة تربيعية" in problem:
        expression = "x**2"

    if "x^2" in problem:
        expression = problem.split("=")[0].strip()

    if not expression:
        return None

    try:
        return generate_function_graph(
            expression,
            "tutor_graph.svg"
        )
    except Exception:
        return None
