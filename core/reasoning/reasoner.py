from core.models import LLM


class Reasoner:

    def __init__(self):

        self.llm = LLM()


    def answer(
        self,
        question,
        knowledge,
    ):

        if not knowledge:

            return "لم أجد معلومات."

        prompt = f"""
أنت مساعد ذكي.

اعتمد فقط على المعلومات التالية.

إذا لم تجد الإجابة داخلها فقل:
"لا أعرف."

========================

{knowledge}

========================

السؤال:

{question}

الإجابة:
"""

        return self.llm.ask(
            prompt
        )


    def analyze(
        self,
        goal,
        report,
        memory,
    ):

        prompt = f"""
أنت العقل الداخلي لوكيل ذكي.

حلل حالة المهمة التالية.

الهدف:
{goal}

التقرير:
{report}

الذاكرة:
{memory}

حدد:
1- سبب النجاح أو الفشل.
2- هل نحتاج خطة جديدة؟
3- ما أفضل اتجاه للخطوة القادمة؟

أعط تحليلًا مختصرًا وواضحًا.
"""

        return self.llm.ask(
            prompt
        )
