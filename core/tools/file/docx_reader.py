from docx import Document


def read_docx(path):
    """
    قراءة ملفات Word (.docx)
    """

    try:

        doc = Document(path)

        text = []

        for paragraph in doc.paragraphs:

            if paragraph.text.strip():
                text.append(paragraph.text)

        return "\n".join(text)

    except Exception as e:

        return f"❌ خطأ في قراءة DOCX:\n{e}"
