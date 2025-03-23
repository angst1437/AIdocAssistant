from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Inches

def mm_to_inches(mm):
    return Inches(mm / 25.4)

class DocBuilder:
    def __init__(self):
        self.doc = Document()

    def change_indent(self):
        for section in self.doc.sections:
            section.left_margin = mm_to_inches(30)  # Левое поле 30 мм
            section.right_margin = mm_to_inches(15)  # Правое поле 15 мм
            section.top_margin = mm_to_inches(20)  # Верхнее поле 20 мм
            section.bottom_margin = mm_to_inches(20)  # Нижнее поле 20 мм

    def get_gost_style(self):
        gost_style = self.doc.styles.add_style('GOST', WD_STYLE_TYPE.PARAGRAPH)
        gost_style.font.name = 'Times New Roman'
        gost_style.font.size = Pt(14)
        gost_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        gost_style.paragraph_format.first_line_indent = mm_to_inches(12.5)
        return gost_style



