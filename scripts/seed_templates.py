import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from web.app import create_app, db
from web.app.models import DocumentTemplate, DocumentSection

def init_templates():
    app = create_app()
    with app.app_context():
        # Проверяем, есть ли уже шаблоны
        if DocumentTemplate.query.count() > 0:
            print("Шаблоны уже существуют. Пропускаем инициализацию.")
            return

        # Создаем шаблон ГОСТ 7.32-2017
        gost_template = DocumentTemplate(
            name="ГОСТ 7.32-2017",
            description="Стандартная структура отчета о научно-исследовательской работе согласно ГОСТ 7.32-2017"
        )
        db.session.add(gost_template)
        db.session.flush()  # Получаем ID шаблона

        # Создаем секции для шаблона
        sections = [
            {
                "name": "Титульный лист",
                "code": "ТЛ",
                "slug": "title-page",
                "description": "Титульный лист отчета о НИР",
                "order": 1,
                "editor_type": 2,  # Форма
                "form_schema": [
                    {
                        "name": "organization",
                        "label": "Наименование организации-исполнителя",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "udk",
                        "label": "УДК",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "reg_number",
                        "label": "Регистрационный номер",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "inv_number",
                        "label": "Инвентарный номер",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "approve_person",
                        "label": "УТВЕРЖДАЮ (должность, ФИО)",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "approve_date",
                        "label": "Дата утверждения",
                        "type": "date",
                        "required": True
                    },
                    {
                        "name": "report_title",
                        "label": "Наименование отчета",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "report_type",
                        "label": "Вид отчета",
                        "type": "select",
                        "required": True,
                        "options": [
                            {"value": "interim", "label": "промежуточный"},
                            {"value": "final", "label": "заключительный"}
                        ]
                    },
                    {
                        "name": "contract_number",
                        "label": "Номер контракта/договора",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "research_manager",
                        "label": "Руководитель НИР (должность, ФИО)",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "city",
                        "label": "Город",
                        "type": "text",
                        "required": True
                    },
                    {
                        "name": "year",
                        "label": "Год",
                        "type": "text",
                        "required": True
                    }
                ]
            },
            {
                "name": "Список исполнителей",
                "code": "СИ",
                "slug": "executors",
                "description": "Список исполнителей отчета о НИР",
                "order": 2,
                "editor_type": 1,  # Форма
                "form_schema": [
                    {
                        "name": "executors",
                        "label": "Список исполнителей (ФИО, должность, ученая степень, ученое звание, подпись)",
                        "type": "textarea",
                        "required": True
                    }
                ]
            },
            {
                "name": "Реферат",
                "code": "Р",
                "slug": "abstract",
                "description": "Реферат отчета о НИР",
                "order": 3,
                "editor_type": 3,  # Смешанный
                "form_schema": [
                    {
                        "name": "keywords",
                        "label": "Ключевые слова",
                        "type": "text",
                        "required": True,
                        "help_text": "Введите ключевые слова через запятую"
                    }
                ]
            },
            {
                "name": "Содержание",
                "code": "С",
                "slug": "table-of-contents",
                "description": "Содержание отчета о НИР",
                "order": 4,
                "editor_type": 1,  # Форма
                "form_schema": []  # Будет заполнено динамически
            },
            {
                "name": "Термины и определения",
                "code": "ТО",
                "slug": "terms",
                "description": "Термины и определения, используемые в отчете",
                "order": 5,
                "editor_type": 3,  # Смешанный
                "form_schema": [
                    {
                        "name": "terms",
                        "label": "Термины и определения",
                        "type": "array",
                        "items": {
                            "term": {
                                "label": "Термин",
                                "type": "text",
                                "required": True
                            },
                            "definition": {
                                "label": "Определение",
                                "type": "textarea",
                                "required": True
                            }
                        }
                    }
                ]
            },
            {
                "name": "Перечень сокращений и обозначений",
                "code": "ПСО",
                "slug": "abbreviations",
                "description": "Перечень сокращений и обозначений, используемых в отчете",
                "order": 6,
                "editor_type": 3,  # Смешанный
                "form_schema": [
                    {
                        "name": "abbreviations",
                        "label": "Сокращения и обозначения",
                        "type": "array",
                        "items": {
                            "abbr": {
                                "label": "Сокращение/обозначение",
                                "type": "text",
                                "required": True
                            },
                            "description": {
                                "label": "Расшифровка",
                                "type": "text",
                                "required": True
                            }
                        }
                    }
                ]
            },
            {
                "name": "Введение",
                "code": "В",
                "slug": "introduction",
                "description": "Введение отчета о НИР",
                "order": 7,
                "editor_type": 2,  # Редактор с ИИ
                "form_schema": None
            },
            {
                "name": "Основная часть",
                "code": "ОЧ",
                "slug": "main",
                "description": "Основная часть отчета о НИР",
                "order": 8,
                "editor_type": 2,  # Редактор с ИИ
                "form_schema": None
            },
            {
                "name": "Заключение",
                "code": "З",
                "slug": "conclusion",
                "description": "Заключение отчета о НИР",
                "order": 9,
                "editor_type": 2,  # Редактор с ИИ
                "form_schema": None
            },
            {
                "name": "Список использованных источников",
                "code": "СЛ",
                "slug": "bibliography",
                "description": "Список использованных источников",
                "order": 10,
                "editor_type": 3,  # Смешанный
                "form_schema": [
                    {
                        "name": "sources",
                        "label": "Источники",
                        "type": "array",
                        "items": {
                            "author": {
                                "label": "Автор(ы)",
                                "type": "text",
                                "required": True
                            },
                            "title": {
                                "label": "Название",
                                "type": "text",
                                "required": True
                            },
                            "publisher": {
                                "label": "Издательство",
                                "type": "text",
                                "required": False
                            },
                            "year": {
                                "label": "Год издания",
                                "type": "text",
                                "required": True
                            },
                            "pages": {
                                "label": "Страницы",
                                "type": "text",
                                "required": False
                            },
                            "url": {
                                "label": "URL",
                                "type": "text",
                                "required": False
                            },
                            "comment": {
                                "label": "Комментарий",
                                "type": "textarea",
                                "required": False
                            }
                        }
                    }
                ]
            },
            {
                "name": "Приложения",
                "code": "П",
                "slug": "appendices",
                "description": "Приложения к отчету о НИР",
                "order": 11,
                "editor_type": 3,  # Смешанный
                "form_schema": [
                    {
                        "name": "appendices",
                        "label": "Приложения",
                        "type": "array",
                        "items": {
                            "title": {
                                "label": "Название приложения",
                                "type": "text",
                                "required": True
                            },
                            "content": {
                                "label": "Содержимое",
                                "type": "editor",
                                "required": True
                            }
                        }
                    }
                ]
            }
        ]

        for section_data in sections:
            section = DocumentSection(
                template_id=gost_template.id,
                name=section_data["name"],
                code=section_data["code"],
                slug=section_data["slug"],
                description=section_data["description"],
                order=section_data["order"],
                editor_type=section_data["editor_type"],
                form_schema=section_data.get("form_schema")
            )
            db.session.add(section)

        db.session.commit()
        print("Шаблоны успешно инициализированы.")

if __name__ == "__main__":
    init_templates()

