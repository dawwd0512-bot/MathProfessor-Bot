from PIL import Image
import pytesseract


def read_image(path):

    try:

        image = Image.open(path)

        text = pytesseract.image_to_string(
            image,
            lang="ara"
        )

        if text.strip():

            return text


        return "❌ لم يتم العثور على نص داخل الصورة."


    except Exception as e:

        return f"❌ خطأ في قراءة الصورة:\n{e}"
