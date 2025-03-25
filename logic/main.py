from builder import DocBuilder
from datatypes import TitleData
from partition import DocPartition
from docx import Document

doc = Document()

doc_builder = DocBuilder()
doc_part = DocPartition("../doc.docx")

parts = doc_part.make_partition()
print(parts)

title = TitleData(
    university_info=["Челябинский Государственный Университет", "Институт информационных технологий", "Факультет приколов"],
    work_type="реферат",
    subject="Физическая культура",
    theme="Фактор горнолыжного спорта в Советском союзе",
    author="Клепцов Александр",
    group="Пи-201",
    educator="Женщина",
    city="Челябинск"
)

content = parts["content"]

intro = parts["intro"]

blocks = {
    "title": title,
    "content": content,
    "intro": intro,
}

doc_builder.build(blocks)