from docx import Document
import docx2pdf
import PyPDF2
import re
import llama
import os


class DocPartition:

    # TODO: сделать чтение одноразовым. Когда будут готовы функции на полное деление документа, их надо объеденить в одну.

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

    def make_partition(self):
        # placeholder для функции сегментации документа
        pass

    def get_title(self):
        """
        Функция получает титульный лист через первую страницу pdf. Сам текст берется в docx, т.к. получение текста из пдф
        периодически имеет артефакты.
        """

        title = []

        with open(self.pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pdf_title_end = reader.pages[0].extract_text().split()[-1]
        for p in self.doc.paragraphs:
            if p.text.strip() == "":
                continue
            title.append(p.text)
            if p.text.split()[-1] == pdf_title_end.strip():
                return " ".join(title)

    def get_content(self):
        """Функция работает аналогично get_title"""
        content = []
        is_content = False

        with open(self.pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pdf_content_start = reader.pages[1].extract_text().split()[1]
            pdf_content_end = reader.pages[1].extract_text().split()[-1]
            print(pdf_content_start, pdf_content_end.strip())

        for p in self.doc.paragraphs:
            if p.text.strip() == "":
                continue
            if p.text.split()[0] == pdf_content_start:
                is_content = True
            if is_content:
                content.append(p.text)
            if p.text.split()[-1] == pdf_content_end:
                print(p.text.split()[-1])
                return content


if __name__ == '__main__':
    doc_part = DocPartition("../doc.docx")
    title_page = doc_part.get_title()
    content_page = doc_part.get_content()
    print(title_page)
    print(content_page)
    # print(llama.title(input()))
