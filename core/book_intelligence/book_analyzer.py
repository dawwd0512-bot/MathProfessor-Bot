from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Chapter:
    number: int
    title: str
    text: str = ""


@dataclass
class BookAnalysis:
    title: str
    full_summary: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    formulas: List[Dict[str, str]] = field(default_factory=list)
    mind_maps: Dict[str, str] = field(default_factory=dict)
    questions: List[Dict[str, str]] = field(default_factory=list)


class BookAnalyzer:
    def __init__(self, ai_function):
        self.ai_function = ai_function

    def summarize_book(self, text: str) -> str:
        prompt = f"""
أنت محلل كتب أكاديمي.

حلل الكتاب التالي وقدّم تلخيصاً مترابطاً وشاملاً.
لا تخترع أي معلومة غير موجودة في النص.

الكتاب:
{text}

المطلوب:
- الفكرة العامة للكتاب
- أهم المحاور
- أهم المفاهيم
- أهم النتائج
- العلاقة بين الفصول
"""
        return self.ai_function(prompt)

    def summarize_chapter(self, chapter: Chapter) -> str:
        prompt = f"""
لخص الفصل التالي اعتماداً على محتواه فقط.

رقم الفصل: {chapter.number}
العنوان: {chapter.title}

المحتوى:
{chapter.text}

أعطني:
- الفكرة الأساسية
- أهم المفاهيم
- أهم القوانين أو التعريفات
- أهم الأمثلة
- خلاصة الفصل
"""
        return self.ai_function(prompt)

    def extract_formulas(self, text: str) -> str:
        """
        استخراج القوانين من النص الأصلي بدون إعادة صياغة أو اختراع.
        الذكاء الاصطناعي يحدد مواضع القوانين فقط، ثم نحتفظ بالنص الأصلي.
        """

        prompt = f"""
أنت تعمل كمحدد للقوانين الرياضية داخل كتاب أكاديمي.

استخرج من النص التالي القوانين والمعادلات والتعريفات الرياضية
الموجودة حرفياً في النص فقط.

قواعد صارمة:
1. لا تخترع أي قانون.
2. لا تعيد صياغة أي قانون.
3. لا تغير أي رمز.
4. لا تغير أسماء المتغيرات.
5. لا تحسب أو تبسط القانون.
6. لا تستنتج قانوناً غير مكتوب صراحة.
7. إذا لم يوجد قانون واضح، أعد: لا توجد قوانين واضحة.
8. أعد المقاطع الأصلية التي تحتوي على القانون كما ظهرت في النص.
9. لا تضف قوانين من معرفتك.

النص:
{text}
"""

        result = self.ai_function(prompt)

        return result.strip() if result else "لا توجد قوانين واضحة."
    def create_mind_map(self, chapter_text: str) -> str:
        prompt = f"""
أنت محلل أكاديمي.

أنشئ خريطة ذهنية للقسم التالي اعتماداً على محتوى القسم نفسه فقط.

مهم جداً:
- لا تضف أي معلومة غير موجودة في النص.
- لا تخترع أمثلة أو قوانين أو مفاهيم.
- لا تلخص من معرفتك الخارجية.
- استخرج المحاور والعلاقات الموجودة فعلياً في النص.
- حافظ على أسماء الموضوعات والمصطلحات كما وردت في النص قدر الإمكان.
- إذا لم يكن القسم مناسباً لخريطة ذهنية، أعد:
لا توجد حاجة لخريطة ذهنية لهذا القسم.

استخدم الشكل:

الموضوع الرئيسي
├── المحور الأول
│   ├── نقطة
│   └── نقطة
├── المحور الثاني
│   ├── نقطة
│   └── نقطة
└── المحور الثالث
    ├── نقطة
    └── نقطة

القسم:
{chapter_text}
"""
        return self.ai_function(prompt)

    def generate_questions(
        self,
        chapter_text: str,
        count: int = 10,
    ) -> str:
        prompt = f"""
أنشئ {count} سؤالاً تعليمياً من الفصل التالي.

نوّع الأسئلة بين:
- اختيار من متعدد
- صح أو خطأ
- سؤال قصير
- مسائل حل عند وجود مادة مناسبة لذلك

لكل سؤال:
- السؤال
- الخيارات إن وجدت
- الإجابة الصحيحة
- شرح مختصر للإجابة

اعتمد فقط على محتوى الفصل.

الفصل:
{chapter_text}
"""
        return self.ai_function(prompt)

def create_gemini_book_analyzer():
    from core.ai.gemini import ask_gemini

    def ai_function(prompt: str) -> str:
        return ask_gemini(prompt)

    return BookAnalyzer(ai_function)
