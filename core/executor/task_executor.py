from core.ai.math_engine import validate_theoretical_claim
import re
from core.models import LLM
from core.tools.manager import ToolManager

from core.tools.registry.tool_registry import (
    execute_tool,
    get_tool,
)


class TaskExecutor:

    def __init__(self):
        self.tools = ToolManager()
        self.llm = LLM()

    def execute(self, tasks):

        results = []

        for task in tasks:

            if isinstance(task, dict):
                data = task
            else:
                data = task.to_dict()

            tool = data.get("tool")
            text = str(
                data.get(
                    "input",
                    ""
                )
            )

            # ==================================================
            # 1. الأسئلة الشخصية والمحادثة
            # ==================================================

            chat_words = [
                "من أنا",
                "ما اسمي",
                "اسمي",
                "مرحبا",
                "السلام عليكم",
                "اهلا",
                "أهلا",
                "كيف حالك",
                "ماذا تعرف عني",
            ]

            if (
                tool != "chat"
                and any(word in text for word in chat_words)
            ):

                answer = self.llm.ask(text)

                results.append({
                    "success": True,
                    "tool": "chat",
                    "output": answer,
                })

                continue

            # ==================================================
            # 2. حماية Python من الأسئلة الطبيعية
            # ==================================================

            natural_question_words = [
                "ما",
                "لماذا",
                "كيف",
                "اشرح",
                "تعريف",
                "نظرية",
                "قانون",
                "احسب",
                "حل",
                "أوجد",
                "برهن",
                "ما هو",
                "ما هي",
            ]

            if (
                tool == "python"
                and any(
                    word in text
                    for word in natural_question_words
                )
            ):

                answer = self.llm.ask(text)

                results.append({
                    "success": True,
                    "tool": "chat",
                    "output": answer,
                })

                continue

            # ==================================================
            # 3. Chat
            # ==================================================

            if tool == "chat":

                chat_input = data.get(
                    "input",
                    ""
                )

                # أرسل للسياق آخر نتائج التنفيذ حتى يستطيع
                # Chat شرح النتيجة فعلياً، وليس مجرد تكرارها.
                previous_results = []

                for previous in results:
                    if (
                        isinstance(previous, dict)
                        and previous.get("success") is True
                    ):
                        previous_input = previous.get(
                            "input",
                            ""
                        )
                        previous_output = previous.get(
                            "output",
                            ""
                        )

                        previous_results.append(
                            f"المطلوب: {previous_input}\n"
                            f"النتيجة: {previous_output}"
                        )

                if previous_results and isinstance(chat_input, str):
                    chat_input = (
                        f"{chat_input}\n\n"
                        "السياق الرياضي السابق:\n"
                        + "\n".join(previous_results)
                        + "\n\n"
                        "اشرح اعتماداً على هذا السياق. "
                        "إذا كان السؤال عن سبب نتيجة حسابية، "
                        "اشرح العملية الحسابية نفسها خطوة بخطوة."
                    )

                answer = self.llm.ask(chat_input)

                results.append({
                    "success": True,
                    "tool": "chat",
                    "output": answer,
                })

                continue
            # ==================================================
            # 4. محرك الرياضيات
            # ==================================================

            if tool == "math":

                try:

                    from core.ai.math_engine import (
                        solve_super_math,
                        format_result,
                    )

                    math_input = data.get(
                        "input",
                        data.get(
                            "goal",
                            text
                        )
                    )

                    math_result = solve_super_math(
                        math_input
                    )

                    # --------------------------------------------------
                    # المسائل النظرية لا يمكن حلها بالـ SymPy وحده.
                    # نرسلها إلى الـ LLM ليعطي برهاناً كاملاً.
                    # --------------------------------------------------

                    if (
                        isinstance(math_result, dict)
                        and math_result.get("type") == "theoretical"
                    ):

                        theoretical_prompt = f"""
أنت أستاذ رياضيات متخصص في التحليل والجبر والمعادلات
الوظيفية.

حل المسألة الرياضية التالية حلاً كاملاً ودقيقاً:

{math_input}

المطلوب:

1. أوجد جميع الحلول.
2. أثبت أن كل حل وجدته يحقق المعادلة.
3. أثبت أن هذه الحلول هي جميع الحلول الممكنة.
4. لا تفترض قابلية الاشتقاق أو الاستمرارية الإضافية
   إلا إذا كانت معطاة في السؤال.
5. استخدم الاستمرارية المعطاة فقط عندما تحتاج إليها.
6. اكتب البرهان خطوة بخطوة.
7. لا تكتفِ بذكر النتيجة النهائية.
8. انتبه للحالات الخاصة مثل x=0 أو y=0.
9. إذا حصلت على عائلة من الحلول، تحقق من كل أفرادها.
10. إذا كان هناك ثابت يجب تحديده، أثبت قيمته بدقة.

أعطني حلاً رياضياً صارماً باللغة العربية.
"""

                        answer = self.llm.ask(
                            theoretical_prompt
                        )

                        # --------------------------------------------------
                        # Deterministic Mathematical Claim Validation
                        # --------------------------------------------------
                        if (
                            isinstance(answer, str)
                            and answer.strip()
                            and not validate_theoretical_claim(math_input, answer)
                        ):
                            answer = (
                                "تم رفض البرهان المولد آليًا لأن إحدى النتائج "
                                "العددية أو أزواج الحلول المذكورة لا تحقق "
                                "الشروط الرياضية للمسألة."
                            )

                        # --------------------------------------------------
                        # Proof Verification Gate
                        # --------------------------------------------------
                        if (
                            isinstance(answer, str)
                            and answer.strip()
                            and not answer.startswith("OpenRouter Error:")
                            and not answer.startswith("OpenRouter Connection Error:")
                            and not answer.startswith("Gemini Error:")
                            and not answer.startswith("Gemini Connection Error:")
                        ):
                            verification_prompt = f"""
أنت مدقق رياضيات مستقل وصارم.

المسألة الأصلية:
{math_input}

الحل المقترح:
{answer}

تحقق من الحل خطوة بخطوة، خصوصاً:
- التعويض في المعادلة الأصلية.
- صحة كل التحويلات الجبرية.
- اكتمال جميع الحلول.
- الحالات الخاصة.
- القسمة على الصفر.
- أي ادعاء غير مثبت.

أجب في البداية حرفياً:
VERDICT: PASS
أو:
VERDICT: FAIL

ثم اذكر سبب الحكم باختصار.
"""

                            verification = self.llm.ask(
                                verification_prompt
                            )

                            if (
                                not isinstance(verification, str)
                                or "VERDICT: PASS" not in verification.upper()
                            ):
                                retry_prompt = f"""
أعد حل المسألة التالية من الصفر حلاً رياضياً صارماً:

{math_input}

الحل السابق فشل في التحقق.
لا تعتمد عليه.

تحقق من كل نتيجة بالتعويض في المعادلة الأصلية،
وأثبت أن مجموعة الحلول كاملة، وانتبه للحالات الخاصة
والقسمة على الصفر.

أعطني البرهان النهائي باللغة العربية.
"""

                                retry_answer = self.llm.ask(
                                    retry_prompt
                                )

                                if (
                                    isinstance(retry_answer, str)
                                    and retry_answer.strip()
                                    and not retry_answer.startswith("OpenRouter Error:")
                                    and not retry_answer.startswith("OpenRouter Connection Error:")
                                    and not retry_answer.startswith("Gemini Error:")
                                    and not retry_answer.startswith("Gemini Connection Error:")
                                ):
                                    final_verification_prompt = f"""
أنت مدقق رياضيات مستقل.

المسألة:
{math_input}

الحل الجديد:
{retry_answer}

تحقق من صحة الحل بالكامل، وخاصة التعويض واكتمال جميع الحلول.

أجب في البداية حرفياً:
VERDICT: PASS
أو:
VERDICT: FAIL
"""

                                    final_verification = self.llm.ask(
                                        final_verification_prompt
                                    )

                                    if (
                                        isinstance(final_verification, str)
                                        and "VERDICT: PASS" in final_verification.upper()
                                    ):
                                        answer = retry_answer
                                    else:
                                        answer = (
                                            "تعذر التحقق من صحة البرهان "
                                            "بشكل مستقل، لذلك لن أعرض حلاً "
                                            "قد يكون غير صحيح."
                                        )
                                else:
                                    answer = (
                                        "تعذر التحقق من صحة البرهان "
                                        "بشكل مستقل، لذلك لن أعرض حلاً "
                                        "قد يكون غير صحيح."
                                    )

                        if (
                            isinstance(answer, str)
                            and answer.strip()
                            and not answer.startswith(
                                "OpenRouter Error:"
                            )
                            and not answer.startswith(
                                "OpenRouter Connection Error:"
                            )
                            and not answer.startswith(
                                "Gemini Error:"
                            )
                            and not answer.startswith(
                                "Gemini Connection Error:"
                            )
                        ):

                            results.append({
                                "success": True,
                                "tool": "math",
                                "output": answer,
                            })

                        else:

                            results.append({
                                "success": False,
                                "tool": "math",
                                "output": (
                                    "تعذر حل المسألة النظرية "
                                    "بواسطة نموذج اللغة."
                                ),
                            })

                        continue

                    # --------------------------------------------------
                    # المسائل العادية: استخدم SymPy
                    # --------------------------------------------------

                    output = format_result(
                        math_result
                    )

                    if output is None:
                        output = "تعذر حل المسألة رياضياً."

                    results.append({
                        "success": True,
                        "tool": "math",
                          "input": str(math_input),
                        "output": output,
                    })

                    continue

                except Exception as e:

                    results.append({
                        "success": False,
                        "tool": "math",
                        "output": (
                            f"Math Engine Error: "
                            f"{type(e).__name__}: {e}"
                        ),
                    })

                    continue

            # ==================================================
            # 5. GRAPH / PLOT
            # ==================================================

            if tool in ("graph", "generate_function_graph"):

                try:
                    from core.image_generator import (
                        generate_function_graph
                    )

                    graph_input = str(
                        data.get(
                            "input",
                            data.get(
                                "goal",
                                text
                            )
                        )
                    ).strip()

                    # إزالة عبارات الرسم فقط.
                    graph_prefixes = [
                        # الأطول أولاً حتى لا يترك التنوين أو الحركات
                        "مثل بيانياً",
                        "مثل بيانيًا",
                        "مثل بيانيا",
                        "مثّل بيانياً",
                        "مثّل بيانيًا",
                        "مثّل بيانيا",
                        "ارسم بيانياً",
                        "ارسم بيانيًا",
                        "ارسم بيانيا",
                        "ارسم الدالتين",
                        "ارسم الدوال",
                        "ارسم الدالة",
                        "الرسم البياني",
                        "رسم بياني",
                    ]

                    for prefix in graph_prefixes:
                        if graph_input.startswith(prefix):
                            graph_input = graph_input[
                                len(prefix):
                            ].strip()
                            break

                    # y = expression -> expression
                    if "=" in graph_input:
                        left, right = graph_input.split(
                            "=",
                            1
                        )

                        if left.strip().lower() == "y":
                            graph_input = right.strip()

                    graph_input = (
                        graph_input
                        .replace("²", "**2")
                        .replace("³", "**3")
                        .replace("×", "*")
                        .replace("÷", "/")
                        .replace("^", "**")
                    )

                    # ------------------------------------------------
                    # Normalize implicit multiplication for SymPy.
                    # Examples:
                    #   1/6X + 5/3  ->  (1/6)*X + 5/3
                    #   2x + 1      ->  2*x + 1
                    #   3(x+1)      ->  3*(x+1)
                    # ------------------------------------------------
                    graph_input = re.sub(
                        r'(?<=\d)(?=[xXyY])',
                        '*',
                        graph_input
                    )

                    graph_input = re.sub(
                        r'(?<=\d)(?=\()',
                        '*',
                        graph_input
                    )

                    graph_input = re.sub(
                        r'(?<=\))(?=[xXyY\d])',
                        '*',
                        graph_input
                    )

                    graph_input = re.sub(
                        r'(?<=[xXyY])(?=\d)',
                        '*',
                        graph_input
                    )

                    graph_input = graph_input.replace(
                        "X", "x"
                    ).replace(
                        "Y", "y"
                    )


                    # ------------------------------------------------
                    # Step 4 integration:
                    # single function -> existing renderer
                    # multiple functions -> multi-function renderer
                    # ------------------------------------------------
                    graph_parts = [
                        part.strip()
                        for part in re.split(
                            r"\s*,\s*|\s+و\s+|،",
                            graph_input
                        )
                        if part.strip()
                    ]

                    # Normalize each function separately.
                    # Example:
                    #   x**2 - 4 و y = x + 2
                    # becomes:
                    #   x**2 - 4
                    #   x + 2
                    normalized_parts = []

                    for part in graph_parts:
                        if "=" in part:
                            left, right = part.split("=", 1)
                            if left.strip().lower() == "y":
                                part = right.strip()

                        normalized_parts.append(part.strip())

                    graph_parts = normalized_parts

                    if len(graph_parts) > 1:
                        from core.multi_graph_renderer import (
                            generate_multi_function_graph
                        )

                        graph_path = generate_multi_function_graph(
                            graph_parts,
                            "telegram_multi_graph.svg"
                        )
                    else:
                        graph_path = generate_function_graph(
                            graph_input,
                            "telegram_graph.svg"
                        )

                    results.append({
                        "success": True,
                        "tool": "graph",
                        "input": graph_input,
                        "output": graph_path,
                        "graph_path": graph_path,
                    })

                    continue

                except Exception as e:

                    results.append({
                        "success": False,
                        "tool": "graph",
                        "output": (
                            f"Graph Error: "
                            f"{type(e).__name__}: {e}"
                        ),
                    })

                    continue

            # ==================================================
            # 5. الأدوات المسجلة
            # ==================================================

            if get_tool(tool):

                try:

                    tool_input = data.get(
                        "input",
                        data
                    )

                    print("=" * 60)
                    print("TOOL :", tool)
                    print("INPUT:")
                    print(tool_input)
                    print("=" * 60)

                    output = execute_tool(
                        tool,
                        tool_input
                    )

                    # إذا كانت الأداة أعادت نتيجة منظمة،
                    # لا نغلفها مرة أخرى بلا داعٍ.
                    if (
                        isinstance(output, dict)
                        and "success" in output
                        and "output" in output
                    ):
                        results.append(output)
                    else:
                        results.append({
                            "success": True,
                            "tool": tool,
                            "output": output,
                        })

                    continue

                except Exception as e:

                    results.append({
                        "success": False,
                        "tool": tool,
                        "output": str(e),
                    })

                    continue

            # ==================================================
            # 6. ToolManager كـ fallback
            # ==================================================

            try:

                result = self.tools.execute(
                    data
                )

                results.append(result)

            except Exception as e:

                results.append({
                    "success": False,
                    "tool": tool,
                    "output": str(e),
                })

        return results
