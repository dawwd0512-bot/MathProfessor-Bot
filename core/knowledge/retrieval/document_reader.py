import os


class DocumentReader:

    def __init__(self):
        pass


    def read(self, path):

        try:

            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": "الملف غير موجود"
                }


            extension = (
                os.path.splitext(path)[1]
                .lower()
            )


            if extension == ".pdf":
                return self.read_pdf(path)


            if extension in [
                ".docx",
                ".doc"
            ]:
                return self.read_word(path)


            if extension in [
                ".txt",
                ".md"
            ]:
                return {
                    "success": True,
                    "type": "text",
                    "content": open(
                        path,
                        "r",
                        encoding="utf-8"
                    ).read()
                }


            return {
                "success": False,
                "error": "نوع الملف غير مدعوم"
            }


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }



    def read_pdf(self, path):

        try:
            from pypdf import PdfReader

            reader = PdfReader(path)

            pages = []

            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)

            content = "\n".join(pages)

            return {
                "success": True,
                "type": "pdf",
                "content": content
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }


    def read_word(self, path):

        try:
            from docx import Document

            doc = Document(path)

            text = "\n".join(
                p.text
                for p in doc.paragraphs
            )


            return {
                "success": True,
                "type": "word",
                "content": text
            }


        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
