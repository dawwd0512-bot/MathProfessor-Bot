import re

from core.llm.json_llm import JSONLLM


class TaskAnalyzer:

    def __init__(self):
        self.llm = JSONLLM()

    def analyze(self, message):
        rule = self._rule_based(message)

        if rule is not None:
            return rule

        prompt = f"""
حلل الطلب التالي.

أعد JSON فقط بالشكل التالي:

{{
    "type": "",
    "tool": "",
    "confidence": 0.0,
    "reason": ""
}}

الأدوات المتاحة:
web
knowledge
python
terminal
math
chat

استخدم math عندما يكون الطلب مسألة أو مفهوماً رياضياً يحتاج حلاً أو شرحاً رياضياً.

استخدم knowledge عندما يطلب المستخدم شرح أو تعريف أو معنى مفهوم،
خصوصاً المفاهيم العلمية والرياضية.

استخدم terminal عندما يكون الطلب متعلقاً بـ:
- أوامر النظام
- الملفات
- git
- تشغيل البرامج
- تشغيل الاختبارات
- حالة المشروع

الطلب:
{message}
"""

        try:
            result = self.llm.ask(prompt)

            if (
                isinstance(result, dict)
                and result.get("tool")
            ):
                return result

        except Exception:
            pass

        return self._fallback(message)

    def _rule_based(self, message):

        text = message.lower().strip()

        # ==================================================
        # Pronunciation
        # ==================================================

        pronunciation_patterns = [
            "انطق",
            "انطقلي",
            "انطق لي",
            "النطق",
            "كيف تنطق",
            "كيف لفظ",
            "لفظ",
            "اقرأ لي",
            "اقرالي",
            "اقرأ",
            "pronounce",
            "pronunciation",
        ]

        if any(x in text for x in pronunciation_patterns):
            return {
                "type": "pronunciation",
                "tool": "pronunciation",
                "confidence": 0.99,
                "reason": "Explicit pronunciation request",
            }


        # ==================================================
        # 1. طلب يعتمد على ملف
        # ==================================================

        solve_from_file_patterns = [
            "بدي ابعتلك",
            "بدي أبعثلك",
            "بدي ارسللك",
            "بدي أرسلك",
            "رح ابعتلك",
            "رح أبعثلك",
            "رح ارسلك",
            "رح أرسلك",
        ]

        file_source_patterns = [
            "عن طريق الملف",
            "من الملف",
            "حسب الملف",
            "بالملف",
            "الملف الي",
            "الملف اللي",
            "الملف الذي",
            "الملف المرفق",
            "الملف المرسل",
        ]

        if (
            any(x in text for x in solve_from_file_patterns)
            and any(x in text for x in file_source_patterns)
        ):
            return {
                "type": "math",
                "tool": "math",
                "confidence": 0.99,
                "reason": "Math question using uploaded document as source",
            }

        # ==================================================
        # 2. Document / File Questions
        # ==================================================

        document_query_patterns = [
            "من الملف",
            "من هذا الملف",
            "من الملف المرفق",
            "من الملف المرسل",
            "حسب الملف",
            "بالاعتماد على الملف",
            "التزم بالملف",
            "لا تخرج من الملف",
            "لا تخرج منه",
            "من صفحة",
            "من الصفحات",
            "في الملف",
            "الملف",
        ]

        document_question_patterns = [
            "هاتلي",
            "هات لي",
            "اعطني",
            "أعطني",
            "اذكر",
            "استخرج",
            "لخص",
            "لخصلي",
            "اشرح",
            "ما هي",
            "ما هي خصائص",
            "خصائص",
            "ما المقصود",
            "تعريف",
            "اذكر لي",
        ]

        if (
            any(x in text for x in document_query_patterns)
            and any(x in text for x in document_question_patterns)
        ):
            return {
                "type": "knowledge",
                "tool": "knowledge",
                "confidence": 0.99,
                "reason": "Question explicitly requires answering from uploaded document",
            }

        # ==================================================
        # 3. Translation
        # ==================================================

        translation_patterns = [
            "ترجم",
            "ترجمة",
            "ترجمه",
            "ترجملي",
            "ترجم لي",
            "translate",
            "translation",
        ]

        if any(x in text for x in translation_patterns):
            return {
                "type": "translation",
                "tool": "knowledge",
                "confidence": 0.99,
                "reason": "Translation Rule",
            }

        # ==================================================
        # 2. Terminal / Project
        # ==================================================

        if (
            "git" in text
            or "terminal" in text
            or re.search(r"\bls\b", text)
            or re.search(r"\bpwd\b", text)
            or "mkdir" in text
            or "rm " in text
            or "nano" in text
            or "python -m" in text
            or "حالة المشروع" in text
            or "ملفات المشروع" in text
            or "اعرض ملفات" in text
        ):
            return {
                "type": "terminal",
                "tool": "terminal",
                "confidence": 0.99,
                "reason": "Terminal / Project Rule",
            }

        # ==================================================
        # 3. Python
        # ==================================================

        if (
            "python" in text
            or "كود بايثون" in text
        ):
            return {
                "type": "python",
                "tool": "python",
                "confidence": 0.99,
                "reason": "Python Rule",
            }

        # ==================================================
        # 4. Web
        # ==================================================

        if (
            "ابحث" in text
            or "search" in text
            or "آخر الأخبار" in text
            or "اخر الاخبار" in text
            or "latest" in text
        ):
            return {
                "type": "web",
                "tool": "web",
                "confidence": 0.99,
                "reason": "Web Search Rule",
            }

        # ==================================================
        # Academic / Study Page-Range Questions
        # ==================================================
        # أسئلة الفصول والصفحات والامتحانات لا يجب أن تصل
        # إلى مصنف الرياضيات بالخطأ.
        # ==================================================

        academic_page_patterns = [
            r"ص\s*\d+\s*[-_]\s*\d+",
            r"صفحة\\s*\\d+\\s*(?:إلى|الى|[-_] )\\s*\\d+",
            r"الصفحات\\s*\\d+\\s*(?:إلى|الى|[-_] )\\s*\\d+",
        ]

        academic_context_patterns = [
            "الفصل",
            "للـامتحان",
            "للامتحان",
            "امتحان",
            "الامتحانات",
            "معلومات مهمة",
            "معلومات مهمه",
            "الدراسة",
            "درست",
            "للامتحانات",
        ]

        has_page_range = any(
            re.search(pattern, text)
            for pattern in academic_page_patterns
        )

        has_academic_context = any(
            pattern in text
            for pattern in academic_context_patterns
        )

        if has_page_range and has_academic_context:
            return {
                "type": "knowledge",
                "tool": "knowledge",
                "confidence": 0.99,
                "reason": "Academic study/page-range question",
            }

        # ==================================================
        # 5. الرياضيات
        # ==================================================
        # هذه القاعدة تأتي قبل المعرفة العامة.
        # أي سؤال رياضي صريح يذهب إلى math.
        # ==================================================

        math_patterns = [
            r"\bاحسب\b",
            r"\bاشتق\b",
            r"\bمشتقة\b",
            r"\bمشتقات\b",
            r"\bتكامل\b",
            r"\bتكاملات\b",
            r"\bمعادلة\b",
            r"\bمعادلات\b",
            r"\bرياضيات\b",
            r"\bرياضي\b",
            r"\bبرهان\b",
            r"\bبراهين\b",
            r"\bاثبت\b",
            r"\bأثبت\b",
            r"\bإثبات\b",
            r"\bفك\b",
            r"\bبسط\b",
            r"\bتبسيط\b",
            r"\bعامل\b",
            r"\bتحليل\b",
            r"\bنهاية\b",
            r"\bنهايات\b",
            r"\bتفاضل\b",
            r"\bتفاضلية\b",
            r"\bاضرب\b",
            r"\bاقسم\b",
            r"\bاجمع\b",
            r"\bاطرح\b",
            r"\bدالة\b",
            r"\bدوال\b",
            r"\bمتباينة\b",
            r"\bمتباينات\b",
            r"\bمصفوفة\b",
            r"\bمصفوفات\b",
            r"\bاحتمال\b",
            r"\bاحتمالات\b",
            r"\bهندسة\b",
            r"\bمثلث\b",
            r"\bمتتاليات\b",
            r"\bمتسلسلات\b",
            r"حل\s+(?:المعادلة|المعادلات|السؤال|المسألة|التمرين)",
            r"أوجد\s+",
            r"اوجد\s+",
        ]

        # ==================================================
        # GRAPH REQUESTS — must be detected BEFORE generic math
        # ==================================================
        graph_patterns = [
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

        if any(pattern in text for pattern in graph_patterns):
            return {
                "type": "graph",
                "tool": "generate_function_graph",
                "confidence": 0.99,
                "reason": "Explicit graph request",
            }

        is_math_text = any(
            re.search(pattern, text)
            for pattern in math_patterns
        )

        has_math_symbols = any(
            ch in text
            for ch in (
                "+",
                "-",
                "*",
                "/",
                "^",
                "=",
                "²",
                "³",
                "√",
                "≤",
                "≥",
                "≠",
                "∫",
                "∞",
            )
        )

        if is_math_text or has_math_symbols:
            return {
                "type": "math",
                "tool": "math",
                "confidence": 0.99,
                "reason": "Math Rule",
            }

        # ==================================================
        # 6. Context — أعلى أولوية عند وجود نتيجة سابقة
        # ==================================================
        # ==================================================
        # 7. Context
        # ==================================================

        context_patterns = [
            "الناتج",
            "النتيجة",
            "السابق",
            "الخطوة السابقة",
            "استخدمها",
            "استخدمه",
            "كمل",
            "أكمل",
            "اكمل",
        ]

        if any(
            pattern in text
            for pattern in context_patterns
        ):
            return {
                "type": "context",
                "tool": "chat",
                "confidence": 0.99,
                "reason": "Context Rule",
            }


        # ==================================================
        # 6. Knowledge / Explanation
        # ==================================================
        # مهم جداً:
        # هذه القاعدة تأتي قبل natural chat.
        #
        # لذلك:
        # "اشرح لي ما هي المشتقة"
        # "شو يعني النهاية؟"
        # "ما المقصود بالتكامل؟"
        #
        # لن يتم اعتبارها Chat.
        # ==================================================

        knowledge_patterns = [
            "اشرح",
            "شرح",
            "فسر",
            "فسّر",
            "تفسير",
            "عرف",
            "عرّف",
            "تعريف",
            "ما هو",
            "ما هي",
            "ماذا يعني",
            "ماذا تعني",
            "ما معنى",
            "ما المقصود",
            "شو المقصود",
            "ايش المقصود",
            "إيش المقصود",
            "شو يعني",
            "ايش يعني",
            "إيش يعني",
            "شو معناها",
            "شو معناه",
            "ايش معناها",
            "ايش معناه",
            "وضح",
            "وضّح",
            "وضحلي",
            "وضّحلي",
            "فهمني",
            "كيف يعمل",
            "كيف تعمل",
        ]

        if any(
            pattern in text
            for pattern in knowledge_patterns
        ):
            return {
                "type": "knowledge",
                "tool": "knowledge",
                "confidence": 0.95,
                "reason": "Knowledge Explanation Rule",
            }

        # ==================================================
        # 8. المحادثة الطبيعية
        # ==================================================

        natural_chat_exact = [
            "مرحبا",
            "أهلا",
            "اهلا",
            "السلام عليكم",
            "شكرا",
            "شكراً",
            "hello",
            "hi",
            "من انت",
            "من أنت",
            "ما اسمك",
            "شو اسمك",
            "كيف حالك",
        ]

        if text in natural_chat_exact:
            return {
                "type": "chat",
                "tool": "chat",
                "confidence": 0.99,
                "reason": "Natural Chat Rule",
            }

        # ==================================================
        # 9. Fallback
        # ==================================================

        return None

    def _fallback(self, message):

        return {
            "type": "chat",
            "tool": "chat",
            "confidence": 0.10,
            "reason": "Fallback",
        }
