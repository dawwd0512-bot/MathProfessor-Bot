import asyncio

from core.ai.gemini import ask_gemini


BATCH_SIZE = 8


def _ask(prompt):
    return ask_gemini(prompt, [], {})


async def summarize_book(chunks, question):
    if not chunks:
        return "❌ لا يوجد محتوى كافٍ في الملف."

    print(f"📚 BOOK SUMMARY: {len(chunks)} chunks")

    summaries = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]

        content = "\n\n".join(batch)

        prompt = f"""
أنت مساعد أكاديمي متخصص.

لدينا جزء من كتاب أو محاضرة طويلة.

طلب المستخدم:
{question}

المحتوى الحالي:
{content}

المطلوب:
- استخرج المعلومات المهمة فقط.
- حافظ على أسماء الدروس والفصول والعناوين.
- حافظ على القوانين والتعاريف والأمثلة المهمة.
- لا تخترع أي معلومة غير موجودة في المحتوى.
- إذا كان المحتوى جزءاً من كتاب رياضيات، حافظ على المصطلحات الرياضية.
- اكتب ملخصاً منظماً يمكن دمجه لاحقاً مع أجزاء أخرى.

أعطِ ملخص هذا الجزء فقط.
"""

        try:
            result = await asyncio.to_thread(
                _ask,
                prompt
            )

            if result:
                summaries.append(
                    f"الجزء {i // BATCH_SIZE + 1}:\n{result}"
                )

            print(
                f"✅ summarized batch "
                f"{i // BATCH_SIZE + 1}"
            )

        except Exception as e:
            print(
                f"❌ batch error: {e}"
            )

    if not summaries:
        return "❌ تعذر تلخيص محتوى الملف."

    combined = "\n\n".join(summaries)

    final_prompt = f"""
أنت أستاذ رياضيات ومحلل كتب أكاديمية.

المستخدم طلب:
{question}

هذه ملخصات أجزاء متتابعة من نفس الكتاب:

{combined}

اكتب الآن الإجابة النهائية للمستخدم.

مهم جداً:
- اعتمد فقط على المعلومات الموجودة في الملخصات.
- لا تخترع أسماء دروس أو فصول.
- إذا طلب المستخدم أسماء الدروس، رتّبها بوضوح.
- إذا كان هناك تسلسل أو فصول، حافظ على ترتيبه.
- إذا طلب تلخيص الكتاب، أعطِ ملخصاً منظماً حسب الفصول أو الموضوعات.
- إذا كان الطلب متعلقاً بصفحات محددة، اذكر المعلومات المتعلقة بها.
- لا تقل إنك لا ترى الصفحات إذا كانت موجودة في البيانات.
"""

    try:
        final_answer = await asyncio.to_thread(
            _ask,
            final_prompt
        )

        return final_answer or "\n\n".join(summaries)

    except Exception as e:
        print(
            f"❌ final summary error: {e}"
        )

        return "\n\n".join(summaries)
