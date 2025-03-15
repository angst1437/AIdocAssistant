from docx import Document

def extract_words_from_first_page(docx_path, approx_words_per_page=500, end_markers=None):
    if end_markers is None:
        end_markers = ['Реферат', 'Содержание', 'Введение']

    document = Document(docx_path)
    words = []
    word_count = 0
    page_break_found = False

    for paragraph in document.paragraphs:
        paragraph_text = paragraph.text.strip()

        # Проверяем наличие ключевых слов
        if any(marker in paragraph_text for marker in end_markers):
            break


        page_break_in_runs = False
        for run in paragraph.runs:
            for br in run._element.findall('.//w:br', run._element.nsmap):
                if br.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type') == 'page':
                    page_break_in_runs = True
                    break
            if page_break_in_runs:
                break

        if page_break_in_runs:
            page_break_found = True
            break


        words_in_paragraph = paragraph_text.split()
        words.extend(words_in_paragraph)
        word_count += len(words_in_paragraph)

        if not page_break_found and word_count >= approx_words_per_page:
            break

    return words

def check_title_page(words):
    title_keywords = ['Министерство', 'образования', 'университет', 'факультет', 'кафедра', 'Выполнил', 'студент', 'группы', 'Нормоконтролер', 'Научный', 'руководитель', 'ВЫПУСКНАЯ', 'КВАЛИФИКАЦИОННАЯ', 'РАБОТА', 'ДИССЕРТАЦИЯ' ]
    for word in words:
        if word in title_keywords:
            return True
    return False
