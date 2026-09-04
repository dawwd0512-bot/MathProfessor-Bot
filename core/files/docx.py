import os


def read_docx(file_path):
    try:
        from docx import Document

        if not os.path.exists(file_path):
            return ""

        doc = Document(file_path)

        text = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)

        return "\n".join(text)

    except Exception as e:
        print("DOCX ERROR:", e)
        return ""
