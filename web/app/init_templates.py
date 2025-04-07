from . import create_app, db
from .models import DocumentTemplate, DocumentSection

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
                "description": "Титульный лист отчета о НИР",
                "order": 1,
                "is_form_based": True,
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
                "description": "Список исполнителей отчета о НИР",
                "order": 2,
                "is_form_based": True,
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
                "description": "Реферат отчета о НИР",
                "order": 3,
                "is_form_based": False
            },
            {
                "name": "Содержание",
                "code": "С",
                "description": "Содержание отчета о НИР",
                "order": 4,
                "is_form_based": False
            },
            {
                "name": "Термины и определения",
                "code": "ТО",
                "description": "Термины и определения, используемые в отчете",
                "order": 5,
                "is_form_based": False
            },
            {
                "name": "Перечень сокращений и обозначений",
                "code": "ПСО",
                "description": "Перечень сокращений и обозначений, используемых в отчете",
                "order": 6,
                "is_form_based": False
            },
            {
                "name": "Введение",
                "code": "В",
                "description": "Введение отчета о НИР",
                "order": 7,
                "is_form_based": False
            },
            {
                "name": "Основная часть",
                "code": "ОЧ",
                "description": "Основная часть отчета о НИР",
                "order": 8,
                "is_form_based": False
            },
            {
                "name": "Заключение",
                "code": "З",
                "description": "Заключение отчета о НИР",
                "order": 9,
                "is_form_based": False
            },
            {
                "name": "Список использованных источников",
                "code": "СЛ",
                "description": "Список использованных источников",
                "order": 10,
                "is_form_based": False
            },
            {
                "name": "Приложения",
                "code": "П",
                "description": "Приложения к отчету о НИР",
                "order": 11,
                "is_form_based": False
            }
        ]

        for section_data in sections:
            section = DocumentSection(
                template_id=gost_template.id,
                name=section_data["name"],
                code=section_data["code"],
                description=section_data["description"],
                order=section_data["order"],
                is_form_based=section_data["is_form_based"],
                form_schema=section_data.get("form_schema")
            )
            db.session.add(section)

        db.session.commit()
        print("Шаблоны успешно инициализированы.")

if __name__ == "__main__":
    init_templates()

