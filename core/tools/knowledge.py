from core.tools.base import BaseTool
from core.tools.registry import register

from core.knowledge.engine import KnowledgeEngine
from core.reasoning.reasoner import Reasoner



# ============================================================
# FAST / DETERMINISTIC TRANSLATION
# ============================================================

TRANSLATION_MAP = {
    "identites": "المتطابقات / الهويات (والصحيح غالبًا Identities حسب السياق)",
    "identities": "الهويات / المتطابقات حسب السياق",
    "consider": "اعتبر / ينظر في",
    "terminal": "طرفي / نهائي / الطرفية حسب السياق",
    "intersects": "يتقاطع / تقاطعات",
    "intersect": "يتقاطع / يتقاطع مع",
    "pythagorean theorem": "مبرهنة فيثاغورس",
    "pythagorean theorm": "مبرهنة فيثاغورس (الصحيح: Theorem)",
    "obtain": "يحصل على / أوجد",
    "divide": "يقسم / اقسم",
    "equation": "معادلة",
    "addition": "جمع",
    "addition formulas": "صيغ الجمع",
    "formulas": "صيغ",
    "formules": "صيغ (والصحيح: Formulas)",
    "half angle formulas": "صيغ نصف الزاوية",
    "half angle formules": "صيغ نصف الزاوية (والصحيح: Formulas)",
    "inequalities": "متباينات / لا مساواة",
    "proof": "برهان / إثبات",
    "vertical": "رأسي / عمودي",
    "amplitude": "السعة",
    "vertical amplitude": "السعة الرأسية / العمودية",
    "dived": "غاص / غطس",
}

def _translate_known(text):
    key = " ".join(text.strip().lower().split())

    if key in TRANSLATION_MAP:
        return TRANSLATION_MAP[key]

    # دعم عدة كلمات مفصولة بمسافات
    words = key.split()
    if len(words) > 1:
        translated = []
        found = True

        for word in words:
            if word in TRANSLATION_MAP:
                translated.append(TRANSLATION_MAP[word])
            else:
                found = False
                break

        if found:
            return " ".join(translated)

    return None




# ============================================================
# DIRECT KNOWLEDGE — COMMON MATHEMATICAL CONCEPTS
# ============================================================

_DIRECT_KNOWLEDGE = {
    "المشتقة": (
        "المشتقة في الرياضيات هي معدل التغير اللحظي للدالة "
        "بالنسبة إلى متغيرها، وهي تمثل أيضًا ميل المماس لمنحنى "
        "الدالة عند نقطة معينة."
        "\n\n"
        "مثال بسيط: إذا كانت f(x)=x² فإن مشتقتها f'(x)=2x."
    ),

    "التكامل": (
        "التكامل هو عملية رياضية مرتبطة بجمع كميات صغيرة جدًا، "
        "ويُستخدم مثلًا لحساب المساحات والحجوم، كما أنه العملية "
        "العكسية للاشتقاق في كثير من الحالات."
        "\n\n"
        "مثال: ∫x² dx = x³/3 + C."
    ),
}


def _direct_knowledge_answer(question):
    if not isinstance(question, str):
        return None

    q = question.strip()
    q = q.replace("؟", "?")
    q = q.rstrip("?!").strip()

    if "مشتقة" in q or "المشتقة" in q:
        return _DIRECT_KNOWLEDGE["المشتقة"]

    if "تكامل" in q or "التكامل" in q:
        return _DIRECT_KNOWLEDGE["التكامل"]

    return None

class KnowledgeTool(BaseTool):

    name = "knowledge"

    def __init__(self):
        self.engine = KnowledgeEngine()
        self.reasoner = Reasoner()

    def execute(self, question):
        # --------------------------------------------------------
        # 1. Translation
        # --------------------------------------------------------
        if isinstance(question, str):
            raw = question.strip()

            if raw.lower().startswith("ترجم "):
                term = raw[5:].strip()
                translated = _translate_known(term)

                if translated:
                    return {
                        "success": True,
                        "tool": self.name,
                        "output": translated,
                    }

        # --------------------------------------------------------
        # 2. Direct mathematical knowledge
        # --------------------------------------------------------
        direct_answer = _direct_knowledge_answer(question)

        if direct_answer:
            return {
                "success": True,
                "tool": self.name,
                "output": direct_answer,
            }

        # --------------------------------------------------------
        # 3. General knowledge engine
        # --------------------------------------------------------
        knowledge = self.engine.search_text(question)

        answer = self.reasoner.answer(
            question,
            knowledge
        )

        return {
            "success": True,
            "tool": self.name,
            "output": answer,
        }


register(KnowledgeTool)
