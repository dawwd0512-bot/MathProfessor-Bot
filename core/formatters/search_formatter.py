class SearchFormatter:

    def format(self, result):
        if not result:
            return "لم أجد نتائج."

        # إذا وصلت النتيجة ملفوفة داخل data
        if "data" in result:
            result = result["data"]

        results = result.get("results", [])

        if results:
            text = "🔎 نتائج البحث:\n\n"

            for i, item in enumerate(results, 1):
                text += f"{i}. {item.get('title', 'بدون عنوان')}\n"

                if item.get("url"):
                    text += f"🔗 {item['url']}\n"

                text += "\n"

            return text

        # دعم DuckDuckGo abstract
        abstract = result.get("abstract", "")

        if abstract:
            return f"🔎 {abstract}"

        return "لم أجد نتائج."
