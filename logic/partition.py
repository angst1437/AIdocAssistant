from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import docx2pdf
import PyPDF2
import re
import logic.llama as llama
import os
import json

class DocPartition:

    with open(r"./gost.json", "r", encoding="UTF-8") as f:
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

        self.doc_reader = iter(self.doc.paragraphs)

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

    def is_header(self, paragraph):
        if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER or any(
            [word in paragraph.text.lower().strip() for word in self.keywords]):
            return True
        else:
            return False

    def make_partition(self):
        parts = {
            "title": None,
            "content": None,
            "intro": None,
            "main": None,
            "conclusion": None,
            "sources": None,
            "appendices": None
        }

        pdf_title_end, pdf_content_end = self.read_pdf()
        parts["title"] = self.get_title(pdf_title_end)
        parts["content"] = self.get_content(pdf_content_end)
        parts["intro"], first_part_title = self.get_intro()
        parts["main"] = self.get_main()
        parts["main"].insert(0, first_part_title)
        parts["conclusion"] = self.get_conclusion()
        parts["sources"] = self.get_sources()

        return parts


    def get_title(self, pdf_end):
        title = []
        while True:
            p = next(self.doc_reader)
            if p.text.strip() == "":
                continue
            title.append(p.text.strip())
            if p.text.split()[-1] == pdf_end.strip():
                return title

    def get_content(self, pdf_end):
        content = []
        while True:
            p = next(self.doc_reader)
            if p.text.strip() == "" or p.text.strip().lower() == "содержание":
                continue

            content.append(p.text.strip())
            if p.text.split()[-1] == pdf_end.strip():
                return content

    def get_intro(self):
        intro = []
        while True:
            p = next(self.doc_reader)
            if p.text.strip() == "":
                continue

            if self.is_header(p):
                if p.text.strip().lower() == "введение": continue
                return [intro, p.text.strip()]
            else:
                intro.append(p.text.strip())

    def get_main(self):
        main = []
        temp_container = []
        curr_part = None
        while True:
            p = next(self.doc_reader)
            if p.text.strip() == "":
                continue

            elif self.is_header(p):
                if p.text.strip().lower() == "заключение":
                    main.append(temp_container)
                    return main
                elif llama.check_main_part(p.text.strip()) == "да":
                    main.append(temp_container)
                    curr_part = p.text.split()[0]
                    temp_container.clear()
                    temp_container.append(p.text.strip())
                continue
            else:
                temp_container.append(p.text.strip())

    def get_conclusion(self):
        conclusion = []
        while True:
            p = next(self.doc_reader)
            if p.text.strip() == "":
                continue

            elif self.is_header(p):
                return conclusion

            else:
                conclusion.append(p.text.strip())

    def get_sources(self):
        sources = []
        while True:
            try:
                p = next(self.doc_reader)
                if p.text.strip() == "":
                    continue
                else:
                    sources.append(p.text.strip())
            except StopIteration:
                return sources


    # TODO: сделать функцию get_appendices(возможно различное оформление)

if __name__ == '__main__':
    doc_part = DocPartition("../doc1.docx")
    parts = doc_part.make_partition()
    for key, value in parts.items():
        print(key, value)

