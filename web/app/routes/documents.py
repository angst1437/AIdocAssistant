from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, send_file, current_app, \
    session
from flask_login import login_required, current_user
from web.app import db
from web.app.models import DocumentApp, DocumentTemplate, DocumentSection, DocumentSectionContent
from web.app.services.document_service import DocumentService
from web.app.services.export_service import export_to_docx, export_to_pdf
from web.app.utils.decorators import log_activity
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from docx import Document
import json

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/')
@login_required
def index():
    documents = DocumentApp.query.filter_by(user_id=current_user.id).order_by(DocumentApp.updated_at.desc()).all()
    return render_template('documents/index.html', title='Мои документы', documents=documents)


@documents_bp.route('/create', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='Document creation page accessed')
def create():
    # Перенаправляем на страницу выбора способа создания документа
    return redirect(url_for('documents.create_options'))


@documents_bp.route('/create-options')
@login_required
def create_options():
    """Страница выбора способа создания документа"""
    # Очищаем сессию от предыдущих данных о создании документа
    if 'temp_document_id' in session:
        del session['temp_document_id']

    return render_template('documents/create_options.html', title='Создание документа')


@documents_bp.route('/create-new', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='New document created')
def create_new():
    """Создание нового документа"""
    if request.method == 'POST':
        title = request.form.get('title', 'Новый документ')

        # Проверяем, есть ли уже созданный документ в сессии
        if 'temp_document_id' in session:
            document_id = session['temp_document_id']
            document = DocumentApp.query.get(document_id)

            # Если документ существует и принадлежит текущему пользователю, обновляем его
            if document and document.user_id == current_user.id:
                document.title = title
                db.session.commit()
                return redirect(url_for('documents.select_section', document_id=document.id))

        # Получаем шаблон ГОСТ 7.32-2017
        template = DocumentTemplate.query.filter_by(name="ГОСТ 7.32-2017").first()
        if not template:
            flash('Шаблон ГОСТ 7.32-2017 не найден', 'error')
            return redirect(url_for('documents.create_options'))

        # Создаем новый документ
        document = DocumentService.create_document(title, current_user.id, template.id)

        # Сохраняем ID документа в сессии
        session['temp_document_id'] = document.id

        # Перенаправляем на страницу выбора раздела
        return redirect(url_for('documents.select_section', document_id=document.id))

    return render_template('documents/create_new.html', title='Новый документ')


@documents_bp.route('/<int:document_id>/select-section')
@login_required
def select_section(document_id):
    """Страница выбора раздела для начала работы"""
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    # Получаем все секции шаблона
    sections = DocumentSection.query.filter_by(template_id=document.template_id).order_by(DocumentSection.order).all()

    return render_template('documents/select_section.html',
                           title=f"Выбор раздела - {document.title}",
                           document=document,
                           sections=sections)


@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='Document upload page accessed')
def upload_document():
    """Загрузка существующего документа"""
    if request.method == 'POST':
        if 'document' not in request.files and 'text_content' not in request.form:
            flash('Не выбран файл и не введен текст', 'error')
            return redirect(request.url)

        title = request.form.get('title', 'Новый документ')

        # Проверяем, есть ли уже созданный документ в сессии
        if 'temp_document_id' in session:
            document_id = session['temp_document_id']
            document = DocumentApp.query.get(document_id)

            # Если документ существует и принадлежит текущему пользователю, используем его
            if document and document.user_id == current_user.id:
                document.title = title
                db.session.commit()
            else:
                # Иначе создаем новый документ
                document = create_document_for_upload(title)
        else:
            # Создаем новый документ
            document = create_document_for_upload(title)

        # Сохраняем ID документа в сессии
        session['temp_document_id'] = document.id

        # Обрабатываем загрузку файла или текста
        process_upload(document, request)

        flash('Документ успешно создан', 'success')
        return redirect(url_for('documents.select_section', document_id=document.id))

    return render_template('documents/upload.html', title='Загрузка документа')


def create_document_for_upload(title):
    """Вспомогательная функция для создания документа при загрузке"""
    # Получаем шаблон ГОСТ 7.32-2017
    template = DocumentTemplate.query.filter_by(name="ГОСТ 7.32-2017").first()
    if not template:
        flash('Шаблон ГОСТ 7.32-2017 не найден', 'error')
        return redirect(url_for('documents.create_options'))

    # Создаем новый документ
    return DocumentService.create_document(title, current_user.id, template.id)


def process_upload(document, request):
    """Вспомогательная функция для обработки загрузки файла или текста"""
    # Получаем шаблон ГОСТ 7.32-2017
    template = DocumentTemplate.query.filter_by(name="ГОСТ 7.32-2017").first()

    # Обрабатываем загрузку файла
    if 'document' in request.files:
        file = request.files['document']
        if file and file.filename:
            filename = secure_filename(file.filename)
            if filename.endswith(('.docx', '.pdf', '.txt')):
                # Сохраняем файл временно
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Обрабатываем файл в зависимости от типа
                if filename.endswith('.docx'):
                    try:
                        doc = Document(file_path)
                        content = '\n'.join([para.text for para in doc.paragraphs])

                        # Создаем секцию "Основная часть" с содержимым файла
                        main_section = DocumentSection.query.filter_by(
                            template_id=template.id,
                            slug='main'
                        ).first()

                        if main_section:
                            DocumentService.update_section_content(
                                document.id,
                                main_section.id,
                                current_user.id,
                                f"<p>{content.replace(char(10), '</p><p>')}</p>",
                                {}
                            )
                    except Exception as e:
                        current_app.logger.error(f"Error parsing docx: {str(e)}")

                # Удаляем временный файл
                os.remove(file_path)
            else:
                flash('Неподдерживаемый формат файла', 'error')

    # Обрабатываем текстовое содержимое
    elif 'text_content' in request.form:
        content = request.form.get('text_content', '')
        if content:
            # Создаем секцию "Основная часть" с содержимым текста
            main_section = DocumentSection.query.filter_by(
                template_id=template.id,
                slug='main'
            ).first()

            if main_section:
                DocumentService.update_section_content(
                    document.id,
                    main_section.id,
                    current_user.id,
                    f"<p>{content.replace(char(10), '</p><p>')}</p>",
                    {}
                )


@documents_bp.route('/<int:document_id>/edit')
@login_required
def edit(document_id):
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    # Перенаправляем на страницу структуры документа
    return redirect(url_for('documents.structure', document_id=document_id))


@documents_bp.route('/<int:document_id>/update', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document updated')
def update(document_id):
    # Получаем данные из формы или JSON
    if request.is_json:
        data = request.get_json()
        title = data.get('title')
    else:
        title = request.form.get('title')

    if title:
        success = DocumentService.update_document(document_id, current_user.id, title)
        if not success:
            abort(403)

    return jsonify({'success': True})


@documents_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document deleted')
def delete(document_id):
    success = DocumentService.delete_document(document_id, current_user.id)
    if not success:
        abort(403)

    flash('Документ успешно удален', 'success')
    return redirect(url_for('documents.index'))


@documents_bp.route('/<int:document_id>/structure')
@login_required
def structure(document_id):
    """Страница управления структурой документа"""
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    # Получаем все секции шаблона
    template_sections = DocumentSection.query.filter_by(template_id=document.template_id).order_by(
        DocumentSection.order).all()

    # Получаем существующие секции документа
    existing_sections = {
        content.section_id: content
        for content in DocumentSectionContent.query.filter_by(document_id=document.id).all()
    }

    return render_template('documents/structure.html',
                           title=f"Структура - {document.title}",
                           document=document,
                           template_sections=template_sections,
                           existing_sections=existing_sections)


@documents_bp.route('/<int:document_id>/edit/<string:section_slug>', methods=['GET'])
@login_required
def edit_section(document_id, section_slug):
    """Редактирование секции документа"""
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    # Получаем секцию по slug
    section = DocumentSection.query.filter_by(template_id=document.template_id, slug=section_slug).first_or_404()

    # Получаем или создаем содержимое секции
    section_content = DocumentSectionContent.query.filter_by(
        document_id=document_id,
        section_id=section.id
    ).first()

    if not section_content:
        section_content = DocumentSectionContent(
            document_id=document_id,
            section_id=section.id,
            content='',
            form_data={}
        )
        db.session.add(section_content)
        db.session.commit()

    # Получаем все секции шаблона для навигации
    template_sections = DocumentSection.query.filter_by(template_id=document.template_id).order_by(
        DocumentSection.order).all()

    # Получаем существующие секции документа для навигации
    existing_sections = {
        content.section_id: content
        for content in DocumentSectionContent.query.filter_by(document_id=document.id).all()
    }

    # Выбираем шаблон в зависимости от типа редактора
    if section.editor_type == 1:  # Форма
        if section.slug == 'table-of-contents':
            return render_template('documents/section_toc.html',
                                   title=f"{document.title} - {section.name}",
                                   document=document,
                                   section=section,
                                   section_content=section_content,
                                   template_sections=template_sections,
                                   existing_sections=existing_sections)
        else:
            return render_template('documents/section_form.html',
                                   title=f"{document.title} - {section.name}",
                                   document=document,
                                   section=section,
                                   section_content=section_content,
                                   template_sections=template_sections,
                                   existing_sections=existing_sections)
    elif section.editor_type == 2:  # Редактор с ИИ
        return render_template('documents/section_editor.html',
                               title=f"{document.title} - {section.name}",
                               document=document,
                               section=section,
                               section_content=section_content,
                               template_sections=template_sections,
                               existing_sections=existing_sections)
    elif section.editor_type == 3:  # Смешанный
        if section.slug == 'bibliography':
            return render_template('documents/section_bibliography.html',
                                   title=f"{document.title} - {section.name}",
                                   document=document,
                                   section=section,
                                   section_content=section_content,
                                   template_sections=template_sections,
                                   existing_sections=existing_sections)
        else:
            return render_template('documents/section_mixed.html',
                                   title=f"{document.title} - {section.name}",
                                   document=document,
                                   section=section,
                                   section_content=section_content,
                                   template_sections=template_sections,
                                   existing_sections=existing_sections)


@documents_bp.route('/<int:document_id>/section/<int:section_id>/update', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Section updated')
def update_section(document_id, section_id):
    """Обновление содержимого секции"""
    # Обновляем содержимое в зависимости от типа редактора
    if request.is_json:
        data = request.get_json()
        content = data.get('content')
        form_data = data.get('form_data')
    else:
        # Для форм и смешанных редакторов
        form_data = {}
        for field in request.form:
            if field != 'csrf_token':
                form_data[field] = request.form[field]

        content = request.form.get('content', '')

    success = DocumentService.update_section_content(
        document_id,
        section_id,
        current_user.id,
        content,
        form_data
    )

    if not success:
        abort(403)

    return jsonify({'success': True})


@documents_bp.route('/<int:document_id>/preview')
@login_required
def preview(document_id):
    """Preview document before export"""
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    # Get all sections ordered by their position
    sections = document.sections.order_by(DocumentSectionContent.id).all()
    
    return render_template('documents/preview.html',
                         title=f"Предпросмотр - {document.title}",
                         document=document,
                         sections=sections)


@documents_bp.route('/<int:document_id>/export/<format>', methods=['GET'])
@login_required
@log_activity(level='INFO', message='Document exported')
def export_document(document_id, format):
    """Экспорт документа"""
    document = DocumentService.get_document(document_id, current_user.id)
    if not document:
        abort(403)

    if format == 'docx':
        file_path = export_to_docx(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.docx")
    elif format == 'pdf':
        file_path = export_to_pdf(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.pdf")
    else:
        abort(400, description="Unsupported format")

