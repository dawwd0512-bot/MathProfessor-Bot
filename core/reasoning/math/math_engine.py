class MathEngine:

    def __init__(self):

        self.domains = [
            "algebra",
            "geometry",
            "calculus",
            "linear_algebra",
            "probability",
            "number_theory"
        ]


    def detect_domain(self, question):

        text = question.lower()


        keywords = {

            "geometry": [
                "مثلث",
                "زاوية",
                "دائرة",
                "فيثاغورس",
                "برهان هندسي"
            ],

            "algebra": [
                "معادلة",
                "س",
                "x",
                "حل"
            ],

            "calculus": [
                "تفاضل",
                "تكامل",
                "مشتقة",
                "نهاية"
            ],

            "linear_algebra": [
                "مصفوفة",
                "محدد",
                "متجه"
            ],

            "probability": [
                "احتمال",
                "توزيع",
                "متوسط"
            ],

            "number_theory": [
                "عدد أولي",
                "قاسم",
                "نظرية الأعداد"
            ]

        }


        for domain, words in keywords.items():

            for word in words:

                if word in text:
                    return domain


        return "general"



    def analyze(self, question):

        return {
            "domain": self.detect_domain(question),
            "question": question
        }
