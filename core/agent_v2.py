import re
from core.utils.response_formatter import format_response
from core.ai.gemini import ask_gemini
from core.context.manager import ContextManager
from core.context.resolver import ContextResolver

from core.executor.task_executor import TaskExecutor
from core.formatters.search_formatter import SearchFormatter

from core.planner_v2 import PlannerV2
from core.loop.agent_loop import AgentLoop

from core.mission.mission_manager import MissionManager
from core.state.state_manager import StateManager

from core.memory.conversation_memory import ConversationMemory
from core.memory.memory_store import MemoryStore
from core.memory.knowledge_base import KnowledgeBase

from core.knowledge.retrieval.knowledge_router import KnowledgeRouter
from core.knowledge.retrieval.web_reader import WebReader
from core.knowledge.retrieval.document_reader import DocumentReader
from core.providers.search import SearchProvider

from core.reasoning.math.math_engine import MathEngine
from core.reasoning.math.solver import MathSolver
from core.reasoning.math.proof_engine import ProofEngine

from core.self_improvement.engine import SelfImprovementEngine
from core.self_improvement.supervisor.supervisor import ImprovementSupervisor
from core.self_improvement.execution.safe_executor import SafeExecutor
from core.self_improvement.memory.improvement_memory import ImprovementMemory
from core.self_improvement.autonomous.development_loop import AutonomousDevelopmentLoop
from core.agent_core.core import AgentCore



def _extract_requested_page_range(message, file_context):
    """
    Extract an explicit page range from the user's question and
    restrict file_context to that range only.

    Supports forms such as:
    - من صفحة 5 إلى 32
    - من الصفحات 5 إلى 32
    - صفحات 5-32
    - page 5 to 32
    - pages 5-32
    """
    if not file_context:
        return file_context

    text = str(message)

    patterns = [
        r"(?:من\s+)?(?:صفحة|الصفحة|الصفحات|صفحات|ص)\s*(\d+)\s*(?:إلى|الى|حتى|-|_)\s*(\d+)",
        r"(?:page|pages|p)\s*(\d+)\s*(?:to|-|_)\s*(\d+)",
    ]

    start = end = None

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            break

    if start is None or end is None:
        return file_context

    if start > end:
        start, end = end, start

    lines = str(file_context).splitlines()

    # Recognize common page markers produced by document readers.
    page_pattern = re.compile(
        r"^\s*(?:"
        r"\[?\s*(?:page|صفحة|الصفحة)\s*(\d+)\s*\]?"
        r"|"
        r"---\s*(?:page|صفحة)\s*(\d+)\s*---"
        r")\s*$",
        re.IGNORECASE
    )

    selected = []
    current_page = None

    for line in lines:
        match = page_pattern.match(line)

        if match:
            number = match.group(1) or match.group(2)
            current_page = int(number)

        if current_page is not None and start <= current_page <= end:
            selected.append(line)

    # If page markers exist and we found content, return only the range.
    if selected:
        return "\n".join(selected)

    # Do not silently pretend that a range was extracted.
    # Returning the original context lets Gemini inspect the existing
    # document format instead of destroying the file context.
    return file_context



class AgentV2:

    def __init__(self):

        self.context = ContextManager()
        self.resolver = ContextResolver()

        self.planner = PlannerV2()
        self.executor = TaskExecutor()

        self.loop = AgentLoop(
            self.planner,
            self.executor
        )

        self.formatter = SearchFormatter()

        self.missions = MissionManager()
        self.state = StateManager()

        self.conversation_memory = ConversationMemory()
        self.memory_store = MemoryStore()
        self.knowledge_base = KnowledgeBase()


        # نظام المعرفة والبحث
        self.web_reader = WebReader()
        self.document_reader = DocumentReader()
        self.search_provider = SearchProvider()

        self.knowledge_router = KnowledgeRouter(
            self.knowledge_base,
            self.search_provider,
            self.web_reader,
            self.document_reader
        )


        # نظام التفكير الرياضي
        self.math_engine = MathEngine()
        self.math_solver = MathSolver()
        self.proof_engine = ProofEngine()


        # نظام التطوير الذاتي
        self.self_improvement = SelfImprovementEngine()

        self.supervisor = ImprovementSupervisor(
            self.self_improvement
        )

        self.memory = ImprovementMemory()
        self.safe_executor = SafeExecutor()

        self.autonomous = AutonomousDevelopmentLoop(
            self.self_improvement,
            self.supervisor,
            self.safe_executor,
            self.memory
        )

        # AgentCore: طبقة معزولة فوق المكونات الحالية.
        # لا تستبدل AgentV2 ولا تمس مسار الرياضيات.
        self.agent_core = AgentCore(
            self.conversation_memory,
            self.memory_store,
            self.planner,
            self.executor.tools
        )

        # Runtime bridge: optional only.
        # Existing AgentV2 and math routing remain authoritative.
        self.agent_core_enabled = True


    def evolve(self, goal):

        return self.autonomous.evolve(goal)


    def is_chat_message(self, message):

        import re

        text = " ".join(str(message).strip().split())

        if not text:
            return False

        # ============================================================
        # CASUAL / SMALL TALK
        # ============================================================
        # هذه الرسائل لا يجب أن ترث سياق الملف السابق.
        # القاعدة محافظة: مجاملات وتحيات قصيرة فقط.
        # ============================================================

        if len(text) <= 80:

            casual_patterns = [
                r"^10\s*/\s*10(?:\s+.*)?$",
                r"^100\s*/\s*100(?:\s+.*)?$",
                  r"^جبت\s+10\s*/\s*10(?:\s+.*)?$",
                  r"^أخذت\s+10\s*/\s*10(?:\s+.*)?$",

                r"^(شكرا|شكرًا|شكراً|مشكور|يسلمو|يعطيك العافية|يعطيك العافيه)(?:\s+.*)?$",

                r"^(احسنت|أحسنت|ممتاز|رائع|روعه|روعة|مبدع|برافو|كفو|عاش|تسلم)(?:\s+.*)?$",

                r"^(مرحبا|مرحباً|اهلا|أهلا|اهلاً|أهلاً|هلا|السلام عليكم)(?:\s+.*)?$",
            ]

            if any(
                re.fullmatch(pattern, text, flags=re.IGNORECASE)
                for pattern in casual_patterns
            ):
                return True

        # ============================================================
        # EXISTING NATURAL CHAT
        # ============================================================

        greetings = [
            "مرحبا",
            "السلام عليكم",
            "اهلا",
            "أهلا",
            "hello",
            "hi",
            "شكرا",
            "من انت",
            "ما اسمك",
        ]

        return any(
            word == text.lower()
            for word in greetings
        )


    def simple_chat(self):

        return (
            "أهلاً بك يا داوود.\n"
            "أنا ⚡ Ai Agent ⚡."
                )


    def _extract_response(self, result):

        if not isinstance(result, dict):
            return str(result)

        results = result.get(
            "results",
            []
        )

        if results:

            last = results[-1]

            if isinstance(last, dict):

                output = last.get(
                    "output"
                )

                if isinstance(output, dict):

                    if "output" in output:
                        return str(
                            output["output"]
                        )

                    if "response" in output:
                        return str(
                            output["response"]
                        )

                return str(output)


        if "response" in result:
            return str(
                result["response"]
            )


        return str(result)



    def chat(
        self,
        message,
        user_id="default",
        file_context=None
    ):


        self.conversation_memory.add_message(
            user_id,
            "user",
            message
        )


        if self.is_chat_message(message):

            answer = self.simple_chat()

            self.conversation_memory.add_message(
                user_id,
                "assistant",
                answer
            )

            return {
                "response": answer
            }



        # التخطيط أولاً: نحدد نوع المهمة قبل تشغيل أي محرك.
        analysis = self.planner.analyzer.analyze(message)
        selected_tool = analysis.get("tool", "chat")

        # ============================================================
        # PRONUNCIATION / TTS ROUTE
        # ============================================================
        # النطق مسار مستقل ولا يدخل Knowledge/Gemini.
        # ============================================================

        if selected_tool == "pronunciation":

            pronunciation_text = str(message).strip()

            pronunciation_patterns = [
                "انطق لي",
                "انطقلي",
                "انطق",
                "كيف تنطق",
                "كيف لفظ",
                "النطق",
                "لفظ",
                "اقرأ لي",
                "اقرالي",
                "اقرأ",
                "pronounce",
                "pronunciation",
            ]

            for pattern in pronunciation_patterns:
                pronunciation_text = pronunciation_text.replace(
                    pattern,
                    "",
                    1
                )

            pronunciation_text = pronunciation_text.strip()

            # إزالة الكلمات الوصفية الشائعة فقط.
            for prefix in [
                "كلمة ",
                "هذه الكلمة ",
                "هذا ",
                "هذه ",
            ]:
                if pronunciation_text.startswith(prefix):
                    pronunciation_text = pronunciation_text[len(prefix):].strip()
                    break

            if not pronunciation_text:
                pronunciation_text = str(message).strip()

            return {
                "response": pronunciation_text,
                "pronunciation": pronunciation_text
            }

        # ============================================================
        # FILE-FIRST ACADEMIC ROUTING
        # ============================================================
        # إذا كان هناك ملف مرفوع، فأسئلة المحتوى الأكاديمي للملف
        # يجب أن تستخدم Gemini + file_context مباشرة.
        #
        # الاستثناء الوحيد: مسألة رياضية صريحة.
        # ============================================================

        if file_context:

            # ============================================================
            # ACADEMIC FILE QUESTION PRIORITY
            # ============================================================
            # أسئلة مراجعة/تلخيص/كفاية المعلومات من الملف ليست رياضيات.
            # إذا أشار المستخدم صراحةً إلى صفحات أو فصل أو الملف،
            # نضمن بقاء السؤال على مسار الملف.
            # ============================================================

            academic_file_patterns = [
                r"\bمن\s+ص\s*\d+\s*(?:-|_|إلى|الى|حتى)\s*\d+",
                r"\bصفحات?\s*\d+\s*(?:-|_|إلى|الى|حتى)\s*\d+",
                r"\bمن\s+(?:صفحة|الصفحة)\s+\d+\s*(?:-|_|إلى|الى|حتى)\s*\d+",
                "من الملف",
                "في الملف",
                "الفصل",
                "الصفحات",
            ]

            message_text = message.lower()

            explicit_academic_file = any(
                re.search(pattern, message_text)
                for pattern in academic_file_patterns
            )

            if explicit_academic_file:
                selected_tool = "academic_file"

            explicit_math_patterns = [
                r"\bاحسب\b",
                r"\bاشتق\b",
                r"\bمشتقة\b",
                r"\bتكامل\b",
                r"\bمعادلة\b",
                r"\bمعادلات\b",
                r"\bرياضيات\b",
                r"\bبرهان\b",
                r"\bاثبت\b",
                r"\bأثبت\b",
                r"\bتبسيط\b",
                r"\bنهاية\b",
                r"\bتفاضل\b",
                r"\bمصفوفة\b",
                r"\bاحتمال\b",
                r"حل\s+(?:المعادلة|المعادلات|المسألة|التمرين)",
                r"أوجد\s+",
                r"اوجد\s+",
            ]

            message_text = message.lower()

            explicit_math = any(
                re.search(pattern, message_text)
                for pattern in explicit_math_patterns
            )

            has_math_symbols = any(
                ch in message
                for ch in ("=", "+", "*", "/", "^", "²", "³", "√", "∫", "∞")
            )

            if not explicit_math and not has_math_symbols:
                selected_tool = "academic_file"

        # ============================================================
        # GENERAL / ACADEMIC AI PATH
        # ============================================================
        # الرياضيات تبقى على المسار القديم.
        # أما العلوم واللغة والتربية وعلم النفس والأسئلة العامة
        # فتذهب مباشرة إلى Gemini كمدرس عام، مع تمرير الملف إن وجد.
        #
        # هذا يمنع AgentV2 من تحويل كل سؤال غير رياضي إلى مسار
        # Knowledge/Math غير مناسب.
        # ============================================================

        if selected_tool != "math" and selected_tool not in (
            "terminal",
            "python",
            "web",
            "graph",
            "generate_function_graph"
        ):

            try:
                history = self.conversation_memory.get_history(
                    user_id
                )
            except Exception:
                history = []

            memory_profile = self.memory_store.get(
                user_id,
                "profile",
                {}
            )

            academic_prompt = f"""
أنت MathProfessor، مدرس وأستاذ أكاديمي متعدد التخصصات.

أنت متخصص في:
- الرياضيات
- الفيزياء
- علم النفس
- التربية وعلوم التعليم
- اللغة العربية والنحو والبلاغة والأدب
- العلوم والمعرفة العامة

السؤال:
{message}

قواعد مهمة:
1. إذا كان السؤال في علم النفس، أجب كمدرس علم نفس وبأسلوب أكاديمي واضح.
2. إذا كان في الفيزياء، اشرح المفهوم والقوانين والأمثلة عند الحاجة.
3. إذا كان في التربية، اشرح المفاهيم والنظريات بطريقة تعليمية.
4. إذا كان في اللغة العربية، اهتم بالدقة اللغوية والنحوية والبلاغية.
5. إذا كان السؤال عاماً، أجب مباشرة من معرفتك العامة.
6. إذا كان هناك ملف مرفق، استخدمه كمصدر عندما يكون السؤال متعلقاً به.
7. لا تقل إن الملف غير موجود إذا تم تزويدك بمحتواه.
8. إذا لم تجد الإجابة في الملف، قل إن المعلومة غير موجودة في الملف.
9. لا تخترع معلومات وتنسبها إلى الملف.
10. اشرح للطالب بطريقة واضحة ومباشرة.
11. لا تحوّل السؤال إلى مسألة رياضية إلا إذا كان السؤال نفسه رياضياً.
12. لا تبدأ بعبارات مثل "بصفتي ذكاءً اصطناعياً".
"""

            if file_context:

                restricted_file_context = _extract_requested_page_range(
                    message,
                    file_context
                )

                academic_prompt += f"""

المصدر المرفق هو المصدر الوحيد المسموح باستخدامه في هذا السؤال.

إذا طلب المستخدم نطاق صفحات محدداً:
- التزم بهذه الصفحات فقط.
- لا تستخدم أي معلومة من صفحات خارج النطاق.
- لا تستخدم معرفتك العامة لتعويض معلومة غير موجودة في الصفحات المطلوبة.
- إذا لم تجد الإجابة داخل الصفحات المطلوبة، قل بوضوح:
  "المعلومة غير موجودة في الصفحات المحددة من الملف."

الملف ضمن النطاق المطلوب:
--------------------
{restricted_file_context}
--------------------
"""

            answer = ask_gemini(
                academic_prompt,
                history=history,
                memory=memory_profile,
                file_context=None
            )

            self.conversation_memory.add_message(
                user_id,
                "assistant",
                answer
            )

            return {
                "response": format_response(answer)
            }


        resolved = self.resolver.resolve(
            message,
            self.context.history()
        )


        memory = self.memory_store.get(
            user_id,
            "profile",
            {}
        )


        knowledge = None
        retrieved = None

        # هذه القيم كانت تُستخدم في بناء resolved
        # دون أن يتم تعريفها في المسار الحالي.
        # نتركها فارغة مؤقتاً حتى يستمر المسار القديم
        # عبر loop.run() دون كسر AgentV2.
        math_analysis = ""
        math_solution = ""
        math_proof = None

        # المعرفة/الملف تُسترجع عند الحاجة فقط.
        # نسمح أيضاً بالاسترجاع مع الرياضيات عندما يكون السؤال
        # مرتبطاً بملف، حتى يصبح الملف مصدراً للمسألة الرياضية.
        if selected_tool in ("knowledge", "math"):

            knowledge = self.knowledge_base.search(
                user_id,
                message
            )

            retrieved = self.knowledge_router.answer_source(
                user_id,
                message
            )


        resolved += (
            "\n\nتحليل رياضي:\n"
            f"{math_analysis}"
        )


        resolved += (
            "\n\nحل رياضي:\n"
            f"{math_solution}"
        )


        if math_proof:

            resolved += (
                "\n\nبرهان:\n"
                f"{math_proof}"
            )


        if memory:

            resolved += (
                "\n\nمعلومات المستخدم:\n"
                f"{memory}"
            )


        if knowledge:

            resolved += (
                "\n\nمعرفة مرتبطة:\n"
                f"{knowledge}"
            )


        if retrieved:

            resolved += (
                "\n\nمصدر مسترجع:\n"
                f"{retrieved}"
            )


        self.context.add_user(
            message
        )


        mission = self.missions.create(
            goal=resolved,
            goals=[]
        )


        self.state.update(
            "last_mission",
            mission.id
        )


        self.state.update(
            "last_message",
            message
        )


        try:

            result = self.loop.run(
                message,
                self.context.history()
            )


            self.self_improvement.observe(
                {
                    "success": True,
                    "message": "Mission completed"
                }
            )


            final_answer = self._extract_response(
                result
            )

            final_answer = format_response(final_answer)


            self.conversation_memory.add_message(
                user_id,
                "assistant",
                final_answer
            )


            return {
                "response": final_answer,
                "raw": result
            }


        except Exception as e:

            return {
                "error": str(e)
            }
