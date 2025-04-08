import json
import click
# Замените 'web.app' и 'web.app.models' на актуальный путь к вашему Flask приложению и моделям SQLAlchemy
from web.app import db
from web.app.models import DocumentTemplate, DocumentSection

# --- Определяем типы редакторов для консистентности ---
# Настройте числовые значения в соответствии с вашей реализацией
EDITOR_TYPE_RICH_TEXT = 1 # Для секций с преимущественно свободным текстом (Введение, Основная часть, Заключение)
EDITOR_TYPE_FORM = 2      # Для секций с жестко структурированными полями (Титульный лист)
EDITOR_TYPE_MIXED = 3     # Для секций, сочетающих структурированные поля и текст/списки (Реферат, Исполнители, Термины, Сокращения, Библиография, Приложения)
EDITOR_TYPE_GENERATED = 4 # Специальный тип для автоматически генерируемых секций (Содержание)

def run_seed():
    """
    Инициализирует базу данных шаблоном DocumentTemplate и секциями DocumentSections
    для ГОСТ 7.32-2017.
    """
    template_name = "ГОСТ 7.32-2017"
    # --- Проверка на существование (Идемпотентность) ---
    existing_template = DocumentTemplate.query.filter_by(name=template_name).first()
    if existing_template:
        click.echo(f"Шаблон '{template_name}' уже существует. Пропускаем инициализацию.")
        return True # Успех, так как шаблон уже есть

    click.echo(f"Создание шаблона '{template_name}'...")
    # --- Создание шаблона ---
    gost_template = DocumentTemplate(
        name=template_name,
        description="Стандартная структура отчета о НИР согласно ГОСТ 7.32-2017"
    )
    db.session.add(gost_template)
    try:
        db.session.flush() # Получаем ID шаблона перед добавлением секций
    except Exception as e:
        db.session.rollback()
        click.echo(f"Ошибка при добавлении шаблона '{template_name}': {e}", err=True)
        return False

    # --- Определение данных секций ---
    # Примечание: Правила форматирования (центровка, жирность, курсив, интервалы),
    # упомянутые в ГОСТ, обрабатываются при рендеринге документа (генерация PDF/HTML),
    # а не определяются в этой структуре данных. Эта структура определяет, *какие* данные собирать.
    sections_data = [
        # --- ОБЯЗАТЕЛЬНЫЕ СЕКЦИИ ---
        {
            "name": "Титульный лист", "code": "ТЛ", "slug": "title-page",
            "description": "Титульный лист согласно ГОСТ 7.32-2017, п. 5.1, 6.10",
            "order": 1, "editor_type": EDITOR_TYPE_FORM, "is_mandatory": True,
            "form_schema": json.dumps([
                # Шапка (по центру)
                {"name": "ministry", "label": "Министерство/Ведомство (если применимо)", "type": "text", "required": False, "help_text": "Полное наименование, с прописной буквы, по центру."},
                {"name": "org_full_name", "label": "Полное наименование организации-исполнителя", "type": "text", "required": True, "help_text": "ПРОПИСНЫМИ БУКВАМИ, по центру."},
                {"name": "org_short_name", "label": "Сокращенное наименование (в скобках)", "type": "text", "required": False, "help_text": "(ПРОПИСНЫМИ БУКВАМИ), по центру, на отдельной строке."},
                # Идентификаторы (слева)
                {"name": "udk", "label": "УДК", "type": "text", "required": True, "help_text": "Индекс УДК по ГОСТ 7.90, слева."},
                {"name": "reg_nir_number", "label": "Рег. номер НИР", "type": "text", "required": True, "help_text": "Напр., номер ЕГИСУ НИОКТР. Слева."},
                {"name": "reg_report_number", "label": "Рег. номер отчета", "type": "text", "required": True, "help_text": "Напр., номер ИКРБС. Слева."},
                # Блоки Утверждения/Согласования (под идентификаторами)
                # Согласование (слева)
                {"name": "agreement_block_present", "label": "Блок СОГЛАСОВАНО присутствует?", "type": "checkbox", "default": False, "required": False}, # Необязательный блок
                {"name": "agreement_officer_position", "label": "СОГЛАСОВАНО: Должность", "type": "text", "required": False, "depends_on": "agreement_block_present"},
                {"name": "agreement_officer_degree", "label": "СОГЛАСОВАНО: Ученая степень", "type": "text", "required": False, "depends_on": "agreement_block_present"},
                {"name": "agreement_officer_rank", "label": "СОГЛАСОВАНО: Ученое звание", "type": "text", "required": False, "depends_on": "agreement_block_present"},
                {"name": "agreement_officer_name", "label": "СОГЛАСОВАНО: И.О. Фамилия", "type": "text", "required": False, "depends_on": "agreement_block_present"},
                {"name": "agreement_date", "label": "Дата согласования", "type": "date", "required": False, "depends_on": "agreement_block_present", "help_text": "Формат ДД.ММ.ГГГГ"},
                # Утверждение (справа)
                {"name": "approval_officer_position", "label": "УТВЕРЖДАЮ: Должность", "type": "text", "required": True},
                {"name": "approval_officer_degree", "label": "УТВЕРЖДАЮ: Ученая степень", "type": "text", "required": False},
                {"name": "approval_officer_rank", "label": "УТВЕРЖДАЮ: Ученое звание", "type": "text", "required": False},
                {"name": "approval_officer_name", "label": "УТВЕРЖДАЮ: И.О. Фамилия", "type": "text", "required": True},
                {"name": "approval_date", "label": "Дата утверждения", "type": "date", "required": True, "help_text": "Формат ДД.ММ.ГГГГ"},
                # Заголовки отчета (по центру)
                {"name": "doc_type_header", "label": "Вид документа (Заголовок)", "type": "static-text", "value": "ОТЧЕТ", "help_text": "Отображается ПРОПИСНЫМИ, по центру."}, # Используем static-text для неизменяемых частей
                {"name": "doc_type_main", "label": "Вид документа (Основной)", "type": "static-text", "value": "О НАУЧНО-ИССЛЕДОВАТЕЛЬСКОЙ РАБОТЕ", "help_text": "Отображается ПРОПИСНЫМИ, по центру, на след. строке."},
                {"name": "nir_name", "label": "Наименование НИР", "type": "textarea", "required": True, "help_text": "Строчными буквами с первой прописной, по центру."},
                {"name": "report_name_prefix", "label": "Префикс наименования отчета", "type": "static-text", "value": "по теме:", "help_text": "Приводится строчными, если наименование отчета отличается от НИР."},
                {"name": "report_name", "label": "Наименование отчета", "type": "textarea", "required": False, "help_text": "ПРОПИСНЫМИ БУКВАМИ, по центру. Заполняется, если отличается от наименования НИР."},
                {"name": "report_type", "label": "Вид отчета", "type": "select", "required": True, "options": [
                    {"value": "interim", "label": "промежуточный"}, {"value": "final", "label": "заключительный"}
                ], "help_text": "Указывается в круглых скобках."},
                {"name": "interim_stage", "label": "Этап (для промежуточного)", "type": "text", "required": False, "help_text": "Указывается в тех же скобках через запятую, напр.: (промежуточный, этап 2)."},
                {"name": "program_theme_id", "label": "Номер (шифр) программы, темы", "type": "text", "required": False, "help_text": "Прописными буквами, по центру."},
                {"name": "book_number", "label": "Номер книги (тома)", "type": "number", "min": 1, "required": False, "help_text": "Для отчета из >1 книги. Напр.: Книга 2."},
                # Руководитель (слева должность, справа ФИО)
                {"name": "supervisor_position", "label": "Руководитель НИР: Должность", "type": "text", "required": True},
                {"name": "supervisor_degree", "label": "Руководитель НИР: Ученая степень", "type": "text", "required": False},
                {"name": "supervisor_rank", "label": "Руководитель НИР: Ученое звание", "type": "text", "required": False},
                {"name": "supervisor_name", "label": "Руководитель НИР: И.О. Фамилия", "type": "text", "required": True},
                # Подвал (по центру)
                {"name": "city", "label": "Место составления (город)", "type": "text", "required": True, "help_text": "По центру, внизу."},
                {"name": "year", "label": "Год составления", "type": "number", "min": 1900, "max": 2100, "required": True, "help_text": "По центру, внизу, через пробел от города."}
            ], ensure_ascii=False) # Используем ensure_ascii=False для кириллицы
        },
        {
            "name": "Реферат", "code": "РЕФ", "slug": "abstract",
            "description": "Реферат согласно ГОСТ 7.32-2017, п. 5.3, 6.12",
            "order": 3, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": True,
            "form_schema": json.dumps([
                # Метаданные (отображаются первой частью, в строку через запятую)
                {"name": "volume", "label": "Общий объем отчета (стр.)", "type": "number", "min": 1, "required": True},
                {"name": "num_books", "label": "Количество книг", "type": "number", "min": 1, "required": True, "default": 1},
                {"name": "num_figures", "label": "Количество иллюстраций", "type": "number", "min": 0, "required": True},
                {"name": "num_tables", "label": "Количество таблиц", "type": "number", "min": 0, "required": True},
                {"name": "num_sources", "label": "Количество источников", "type": "number", "min": 0, "required": True},
                {"name": "num_appendices", "label": "Количество приложений", "type": "number", "min": 0, "required": False, "default": 0},
                # Ключевые слова (под метаданными, в строку через запятую)
                {"name": "keywords", "label": "Ключевые слова (5-15)", "type": "textarea", "required": True, "help_text": "Введите через запятую, ПРОПИСНЫМИ БУКВАМИ, без точки в конце."},
                # Текст реферата (под ключевыми словами, с абзацами)
                {"name": "abstract_text", "label": "Текст реферата", "type": "editor", "required": True, "help_text": "Оптимально ~850 знаков. Структура: объект, цель, методы, результаты/новизна, область применения, рекомендации/внедрение, эффективность/значимость, прогнозы."}
            ], ensure_ascii=False)
        },
        {
            "name": "Содержание", "code": "СОДЕРЖ", "slug": "table-of-contents",
            "description": "Содержание согласно ГОСТ 7.32-2017, п. 5.4, 6.13 (генерируется автоматически)",
            "order": 4, "editor_type": EDITOR_TYPE_GENERATED, "is_mandatory": True,
            "form_schema": None # Нет прямого редактирования; генерируется приложением
        },
        {
            "name": "Введение", "code": "ВВЕД", "slug": "introduction",
            "description": "Введение согласно ГОСТ 7.32-2017, п. 5.7",
            "order": 7, "editor_type": EDITOR_TYPE_RICH_TEXT, "is_mandatory": True,
            "form_schema": None
        },
        {
            "name": "Основная часть", "code": "ОСН_ЧАСТЬ", "slug": "main",
            "description": "Основная часть согласно ГОСТ 7.32-2017, п. 5.8",
            "order": 8, "editor_type": EDITOR_TYPE_RICH_TEXT, "is_mandatory": True,
            "form_schema": None # Структура (разделы/подразделы) управляется внутри редактора
        },
        {
            "name": "Заключение", "code": "ЗАКЛ", "slug": "conclusion",
            "description": "Заключение согласно ГОСТ 7.32-2017, п. 5.9",
            "order": 9, "editor_type": EDITOR_TYPE_RICH_TEXT, "is_mandatory": True,
            "form_schema": None
        },
        {
            "name": "Список использованных источников", "code": "СПИС_ИСТ", "slug": "bibliography",
            "description": "Список источников согласно ГОСТ 7.32-2017, п. 5.10, 6.16 (формат по ГОСТ 7.1, 7.80, 7.82)",
            "order": 10, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": True,
            "form_schema": json.dumps([
                {
                    "name": "sources", "label": "Источники", "type": "array", "required": True,
                    "help_text": "Нумерация арабскими цифрами с точкой. Порядок - по мере появления ссылок в тексте [1], [2]...",
                    # --- Используем детализированные поля для лучшей структуризации и возможности форматирования ---
                    "items": {
                        "entry_type": {"label": "Тип источника", "type": "select", "required": True, "options": [
                            {"value": "book", "label": "Книга"}, {"value": "article_journal", "label": "Статья в журнале"},
                            {"value": "article_collection", "label": "Статья в сборнике"}, {"value": "thesis", "label": "Диссертация/автореферат"},
                            {"value": "patent", "label": "Патентный документ"}, {"value": "standard", "label": "Стандарт"},
                            {"value": "report", "label": "Отчет о НИР"}, {"value": "website", "label": "Веб-сайт"},
                            {"value": "webpage", "label": "Веб-страница"}, {"value": "conference", "label": "Материалы конференции"},
                            {"value": "other", "label": "Другое"}
                        ]},
                        "authors": {"label": "Автор(ы) или Заголовок", "type": "text", "required": True, "help_text": "Фамилия И.О. Если авторов > 3, указать первого и [и др.]. Если нет автора, начать с Заголовка."},
                        "title": {"label": "Основное заглавие", "type": "text", "required": True, "help_text": "Заглавие книги, статьи, патента, сайта."},
                        "additional_title_info": {"label": "Доп. сведения к заглавию", "type": "text", "required": False, "help_text": "Напр.: : учебник, : материалы конф."},
                        "source_info": {"label": "Сведения об источнике", "type": "text", "required": False, "help_text": "Для статей: // Название журнала (или сборника). Для сайтов: : сайт."},
                        "publication_place": {"label": "Место издания", "type": "text", "required": False, "help_text": "Город (для книг, сборников)."},
                        "publisher": {"label": "Издательство", "type": "text", "required": False, "help_text": "Для книг, сборников."},
                        "year": {"label": "Год издания/публикации", "type": "number", "min": 1500, "required": True},
                        "volume": {"label": "Том (Т.)", "type": "text", "required": False},
                        "issue": {"label": "Номер (№), Выпуск (Вып.)", "type": "text", "required": False},
                        "pages": {"label": "Страницы (С.) или Объем", "type": "text", "required": False, "help_text": "Напр.: С. 25-30 (для статей), 350 с. (для книг)."},
                        "url": {"label": "URL", "type": "url", "required": False, "help_text": "Для электронных ресурсов."},
                        "access_date": {"label": "Дата обращения", "type": "date", "required": False, "help_text": "Для URL: (дата обращения: ДД.ММ.ГГГГ)."},
                        "doi": {"label": "DOI", "type": "text", "required": False}
                    }
                }
            ], ensure_ascii=False)
        },

        # --- НЕОБЯЗАТЕЛЬНЫЕ СЕКЦИИ ---
        {
            "name": "Список исполнителей", "code": "СПИС_ИСПОЛН", "slug": "executors",
            "description": "Список исполнителей согласно ГОСТ 7.32-2017, п. 5.2, 6.11",
            "order": 2, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": False,
            "help_text": "Не оформляется, если отчет выполнен одним исполнителем (п. 5.2.2). Сведения о нем указываются на титульном листе.",
            "form_schema": json.dumps([
                {
                    "name": "executors", "label": "Исполнители", "type": "array", "required": True, # required=True для массива, но сама секция необязательна
                    "help_text": "Располагаются столбцом, формируются в порядке ролей/должностей (руководитель, отв. исп., исп., соисп.).",
                    "items": {
                        "role": {
                            "label": "Роль в НИР", "type": "select", "required": True,
                            "options": [
                                {"value": "supervisor", "label": "Руководитель НИР"},
                                {"value": "lead_executor", "label": "Ответственный исполнитель"},
                                {"value": "executor", "label": "Исполнитель"},
                                {"value": "co_executor", "label": "Соисполнитель"}
                            ], "help_text": "Определяет порядок в списке и ответственность."
                        },
                        "position": {"label": "Должность", "type": "text", "required": True},
                        "degree": {"label": "Ученая степень", "type": "text", "required": False},
                        "rank": {"label": "Ученое звание", "type": "text", "required": False},
                        "name": {"label": "И.О. Фамилия", "type": "text", "required": True},
                        "contribution": {"label": "Вклад (раздел/подраздел)", "type": "text", "required": False, "help_text": "Указать номер раздела (подраздела)."},
                        "organization": {"label": "Организация (если соисполнитель)", "type": "text", "required": False, "help_text": "Указывается для соисполнителей из других организаций."},
                        # Поле для подписи обрабатывается физически/цифровой подписью
                    }
                }
            ], ensure_ascii=False)
        },
        {
            "name": "Термины и определения", "code": "ТЕРМ", "slug": "terms",
            "description": "Термины и определения согласно ГОСТ 7.32-2017, п. 5.5, 6.14",
            "order": 5, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": False,
            "help_text": "Начинается со слов 'В настоящем отчете о НИР применяют следующие термины с соответствующими определениями:'. Оформляется списком.",
            "form_schema": json.dumps([
                {
                    "name": "terms_list", "label": "Термины", "type": "array", "required": True,
                    "help_text": "Рекомендуется располагать термины в алфавитном порядке.",
                    "items": {
                        "term": {"label": "Термин", "type": "text", "required": True, "help_text": "Печатается с абзацного отступа."},
                        "definition": {"label": "Определение", "type": "textarea", "required": True, "help_text": "Печатается через тире после термина."}
                    }
                }
            ], ensure_ascii=False)
        },
        {
            "name": "Перечень сокращений и обозначений", "code": "СОКР", "slug": "abbreviations",
            "description": "Перечень сокращений и обозначений согласно ГОСТ 7.32-2017, п. 5.6, 6.15",
            "order": 6, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": False,
            "help_text": "Начинается со слов 'В настоящем отчете о НИР применяют следующие сокращения и обозначения:'. Включается, если используется более трех условных обозначений.",
            "form_schema": json.dumps([
                {
                    "name": "abbreviations_list", "label": "Сокращения/Обозначения", "type": "array", "required": True,
                    "help_text": "Рекомендуется располагать в алфавитном порядке.",
                    "items": {
                        "abbr": {"label": "Сокращение/Обозначение", "type": "text", "required": True, "help_text": "Печатается с абзацного отступа."},
                        "expansion": {"label": "Расшифровка/Пояснение", "type": "text", "required": True, "help_text": "Печатается через тире."}
                    }
                }
            ], ensure_ascii=False)
        },
        {
            "name": "Приложения", "code": "ПРИЛ", "slug": "appendices",
            "description": "Приложения согласно ГОСТ 7.32-2017, п. 5.11, 6.17",
            "order": 11, "editor_type": EDITOR_TYPE_MIXED, "is_mandatory": False,
            "form_schema": json.dumps([
                {
                    "name": "appendices_list", "label": "Приложения", "type": "array", "required": True,
                    "help_text": "Каждое приложение начинается с новой страницы. Обозначаются последовательно буквами кириллицы (кроме Ё, З, Й, О, Ч, Ъ, Ы, Ь) или латиницы (кроме I, O), или арабскими цифрами.",
                    "items": {
                        "designation": {"label": "Обозначение (А, Б, ...)", "type": "text", "required": True, "help_text": "Напр.: А или 1. Отображается после слова ПРИЛОЖЕНИЕ."},
                        "title": {"label": "Заголовок приложения", "type": "text", "required": True, "help_text": "С прописной буквы, полужирным шрифтом, отдельной строкой по центру."},
                        "content": {"label": "Содержимое приложения", "type": "editor", "required": True, "help_text": "Может включать текст, таблицы, иллюстрации, расчеты и т.д."}
                    }
                }
            ], ensure_ascii=False)
        }
    ]

    # --- Получаем валидные имена колонок из модели DocumentSection ---
    # Используем __table__.columns.keys(), чтобы получить только реальные колонки БД
    valid_section_keys = DocumentSection.__table__.columns.keys()
    # Добавляем 'is_mandatory', так как это поле модели, хоть и не напрямую колонка (если оно есть)
    # Проверим, есть ли оно в атрибутах класса, а не только в колонках
    if hasattr(DocumentSection, 'is_mandatory'):
        valid_section_keys = list(valid_section_keys) + ['is_mandatory']  # Преобразуем в список для добавления

    click.echo(f"Добавление {len(sections_data)} секций для шаблона '{template_name}'...")
    # --- Добавление секций в БД ---
    try:
        for section_data_raw in sections_data:
            # --- Фильтруем словарь перед созданием объекта ---
            section_data_filtered = {
                key: value for key, value in section_data_raw.items()
                if key in valid_section_keys # Оставляем только ключи, соответствующие полям модели
            }
            # --- Убедимся, что form_schema это строка или None ---
            # (Это делаем уже с отфильтрованным словарем, если form_schema есть в valid_section_keys)
            if 'form_schema' in section_data_filtered:
                 schema_value = section_data_filtered.get("form_schema")
                 # Если это не строка и не None (т.е. это еще словарь/список Python), преобразуем в JSON
                 if schema_value is not None and not isinstance(schema_value, str):
                     section_data_filtered["form_schema"] = json.dumps(schema_value, ensure_ascii=False, indent=2)

            # Создаем объект, используя отфильтрованный словарь
            section = DocumentSection(template_id=gost_template.id, **section_data_filtered)
            db.session.add(section)

        db.session.commit()
        click.echo(f"Шаблон '{template_name}' и его секции успешно добавлены.")
        return True
    except Exception as e:
        db.session.rollback()
        click.echo(f"Ошибка при добавлении секций для шаблона '{template_name}': {e}", err=True)
        # Пытаемся удалить шаблон, если добавление секций не удалось
        template_to_delete = db.session.get(DocumentTemplate, gost_template.id) # Используем db.session.get для получения по PK
        if template_to_delete:
            try:
                db.session.delete(template_to_delete)
                db.session.commit()
                click.echo(f"Шаблон '{template_name}' удален из-за ошибки добавления секций.", err=True)
            except Exception as delete_e:
                 db.session.rollback()
                 click.echo(f"Ошибка при удалении шаблона '{template_name}' после ошибки добавления секций: {delete_e}", err=True)
        return False

# --- Пример запуска (адаптируйте под вашу структуру Flask CLI) ---
# Обычно эта функция регистрируется как команда Flask CLI.
# Для прямого тестирования (убедитесь, что БД доступна):
# if __name__ == '__main__':
#     # Здесь может потребоваться настройка контекста приложения Flask
#     from web.app import create_app # Пример
#     app = create_app()
#     with app.app_context():
#          if not run_seed():
#              print("Инициализация не удалась.")
#          else:
#              print("Инициализация завершена.")