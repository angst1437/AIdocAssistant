import json

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import docx2pdf
import PyPDF2
import re
import llama
import os
import json

class DocPartition:

    with open("../gost.json", "r", encoding="UTF-8") as f:
        keywords = json.load(f)["keywords"]

    def __init__(self, file_path):
        """
        Если на вход подается pdf, то создается также конвертация в docx.
        В обратном случае создается конвертация в pdf.
        """
        if re.fullmatch(r'.+\.docx$', file_path):
            self.doc = Document(file_path)
            docx2pdf.convert(file_path)
            self.pdf_path = file_path[:-5] + '.pdf'
        elif re.fullmatch(r'.+\.pdf$', file_path):
            self.pdf_path = file_path
            self.doc = None

    # FIXME: эта залупа работает через раз
    # def __del__(self):
    #     # удаление объекта производит удаление обрабатываемых файлов
    #     os.remove(self.pdf_path)
    #     os.remove(self.pdf_path[:-4] + '.docx')

    def read_pdf(self):
        with open(self.pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pdf_title_end = reader.pages[0].extract_text().split()[-1]
            pdf_content_start = reader.pages[1].extract_text().split()[1]
            pdf_content_end = reader.pages[1].extract_text().split()[-1]
        return [pdf_title_end, pdf_content_end]

    def make_partition(self):
        parts = {}
        unnamed_parts_counter = 0
        unnamed_part_started = False
        temp_container = []
        is_title_read = False
        is_content_read = False
        pdf_title_end, pdf_content_end = self.read_pdf()

        for p in self.doc.paragraphs:
            if p.text.strip() == "":
                continue

            if ((p.alignment == WD_ALIGN_PARAGRAPH.CENTER or any([word in p.text.lower().strip() for word in self.keywords]))
                    and all([is_title_read, is_content_read])):
                print(p.text)
                if unnamed_part_started:
                    parts["part" if unnamed_parts_counter == 0 else "part" + str(unnamed_parts_counter)] = " ".join(temp_container)
                    unnamed_parts_counter += 1
                    temp_container.clear()
                    unnamed_part_started = False

                if not unnamed_part_started:
                    unnamed_part_started = True

            if unnamed_part_started:
                temp_container.append(p.text.strip())


            if not is_title_read:
                temp_container.append(p.text.strip())
                if p.text.split()[-1] == pdf_title_end.strip():
                    parts["title"] = " ".join(temp_container)
                    temp_container.clear()
                    is_title_read = True
                    continue # переход на следующий параграф

            if not is_content_read:
                temp_container.append(p.text.strip())
                if p.text.split()[-1] == pdf_content_end:
                    parts["content"] = " ".join(temp_container)
                    temp_container.clear()
                    is_content_read = True
                    continue  # переход на следующий параграф

        return parts


if __name__ == '__main__':
    doc_part = DocPartition("../doc.docx")
    parts = doc_part.make_partition()
    print(parts)
    for key, value in parts.items():
        print(key, value)
    # print(llama.title(input()))
