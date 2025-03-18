from docx import Document
import docx2pdf
import PyPDF2
import re
import llama

class DocPartition:
    def __init__(self, file_path):
        if re.fullmatch(r'.+\.docx$', file_path):
            self.doc = Document(file_path)
            docx2pdf.convert(file_path)
            self.pdf = file_path[:-5] + '.pdf'
        elif re.fullmatch(r'.+\.pdf$', file_path):
            self.pdf = file_path
            self.doc = None

    def make_partition(self):
        pass

    def get_title(self):
        title = []

        with open(self.pdf, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            pdf_title_end = reader.pages[0].extract_text().split()[-1]
        for p in self.doc.paragraphs:
            if p.text.strip() == "":
                continue
            title.append(p.text)
            if p.text.split()[-1] == pdf_title_end.strip():
                return " ".join(title)


if __name__ == '__main__':
    doc_part = DocPartition("../doc1.docx")
    title_page = doc_part.get_title()
    print(title_page)
    print(llama.title(input()))