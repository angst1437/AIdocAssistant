# Импортируем модели внутри функции, чтобы избежать возможных циклических импортов
# при регистрации команды
def seed_initial_data():
    """Заполняет базу данных начальными данными (шаблоны, секции и т.д.)."""
    from web.app.models import DocumentTemplate, DocumentSection
    from web.app import db

    template_name = "ГОСТ 7.32-2017"
    existing_template = DocumentTemplate.query.filter_by(name=template_name).first()

    if existing_template:
        print(f"Шаблон '{template_name}' уже существует. Пропуск сидинга.")
        return False  # Возвращаем False, если сидинг не выполнен

    print(f"Сидинг базы данных: Создание шаблона '{template_name}'...")

    # --- Создание шаблона ГОСТ ---
    new_template = DocumentTemplate(
        name=template_name,
        description="Стандартный шаблон ГОСТ 7.32-2017 для научно-исследовательских работ"
    )
    db.session.add(new_template)
    # Важно выполнить flush, чтобы получить template_id для секций
    db.session.flush()
    print(f"Создан шаблон с ID: {new_template.id}")

    # --- Определение стандартных секций для ГОСТ ---
    # !!! Адаптируйте этот список под вашу реальную структуру !!!
    sections_data = [
        {'name': 'Титульный лист', 'code': 'ТЛ', 'slug': 'title-page', 'order': 1, 'editor_type': 1,
         'description': 'Форма для заполнения титульного листа.', 'form_schema': {
            'fields': ['university', 'faculty', 'department', 'work_type', 'topic', 'discipline', 'author_group',
                       'author_name', 'supervisor_position', 'supervisor_name', 'city', 'year']}},  # Тип 1 - Форма
        # {'name': 'Реферат', 'code': 'Р', 'slug': 'abstract', 'order': 2, 'editor_type': 2, 'description': 'Краткое изложение содержания работы.'}, # Тип 2 - Редактор
        # {'name': 'Оглавление', 'code': 'О', 'slug': 'table-of-contents', 'order': 3, 'editor_type': 1, 'description': 'Автоматически генерируемое оглавление.'}, # Тип 1 - Специальный (не форма)
        # {'name': 'Определения', 'code': 'ОПР', 'slug': 'definitions', 'order': 4, 'editor_type': 2, 'description': 'Перечень терминов с их определениями.'},
        # {'name': 'Обозначения и сокращения', 'code': 'ОС', 'slug': 'abbreviations', 'order': 5, 'editor_type': 2, 'description': 'Перечень обозначений и сокращений.'},
        {'name': 'Введение', 'code': 'В', 'slug': 'introduction', 'order': 6, 'editor_type': 2,
         'description': 'Актуальность, цели, задачи, объект и предмет исследования.'},  # Тип 2 - Редактор с ИИ
        {'name': 'Основная часть', 'code': 'ОЧ', 'slug': 'main', 'order': 7, 'editor_type': 2,
         'description': 'Теоретические основы, методики, результаты исследования.'},  # Тип 2 - Редактор с ИИ
        {'name': 'Заключение', 'code': 'З', 'slug': 'conclusion', 'order': 8, 'editor_type': 2,
         'description': 'Основные выводы и результаты работы.'},  # Тип 2 - Редактор с ИИ
        {'name': 'Список использованных источников', 'code': 'СИ', 'slug': 'bibliography', 'order': 9, 'editor_type': 3,
         'description': 'Перечень литературы и других источников.'},  # Тип 3 - Смешанный
        # {'name': 'Приложения', 'code': 'П', 'slug': 'appendices', 'order': 10, 'editor_type': 2, 'description': 'Дополнительные материалы (таблицы, иллюстрации).'},
    ]

    # --- Создание секций ---
    for data in sections_data:
        print(f"Добавляем секцию: {data['name']}")
        new_section = DocumentSection(
            template_id=new_template.id,  # Связываем с созданным шаблоном
            name=data['name'],
            code=data['code'],
            slug=data['slug'],
            description=data.get('description', ''),
            order=data['order'],
            editor_type=data['editor_type'],
            form_schema=data.get('form_schema')
        )
        db.session.add(new_section)

    # Сохраняем все изменения в базе данных
    db.session.commit()
    print("Сидинг начальных данных успешно завершен.")
    return True  # Возвращаем True, если сидинг был выполнен