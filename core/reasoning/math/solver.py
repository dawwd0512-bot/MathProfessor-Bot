class MathSolver:


    def solve(self, question):

        text = str(question).lower()



        # نظرية فيثاغورس
        if (
            "فيثاغورس" in text
            or
            "pythagoras" in text
        ):

            return {
                "method": "pythagorean_theorem",
                "formula": "a^2 + b^2 = c^2",
                "message": (
                    "تم تحديد مسألة فيثاغورس. "
                    "أرسل أطوال الضلعين القائمين أو الوتر للحل."
                )
            }



        # هندسة
        if any(
            word in text
            for word in [
                "مثلث",
                "زاوية",
                "دائرة",
                "مستقيم"
            ]
        ):

            return {
                "method": "geometry",
                "message": (
                    "تم تحديد مسألة هندسية."
                )
            }



        # معادلات
        if "=" in text:

            return {
                "method": "algebra",
                "message": (
                    "تم تحديد معادلة جبرية."
                )
            }



        # تكامل
        if "تكامل" in text:

            return {
                "method": "integration",
                "message": (
                    "تم تحديد مسألة تكامل."
                )
            }



        # تفاضل
        if (
            "مشتقة" in text
            or
            "تفاضل" in text
        ):

            return {
                "method": "calculus",
                "message": (
                    "تم تحديد مسألة تفاضل."
                )
            }



        # احتمالات
        if "احتمال" in text:

            return {
                "method": "probability",
                "message": (
                    "تم تحديد مسألة احتمالات."
                )
            }



        return {
            "method": "general",
            "message": (
                "لم أستطع تحديد نوع المسألة."
            )
        }
