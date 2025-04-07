from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort, send_file, current_app
from flask_login import login_required, current_user
from .. import db
from ..models import DocumentBlock, Recommendation, DocumentTemplate, DocumentSection, \
    DocumentSectionContent, DocumentApp, TextRecommendation
from ..utils.decorators import log_activity
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
    return render_template('documents/index.html', title='My Documents', documents=documents)


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
    return render_template('documents/create_options.html', title='Создание документа')


@documents_bp.route('/create-new', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='New document created')
def create_new():
    """Создание нового документа с выбором структуры"""
    if request.method == 'POST':
        title = request.form.get('title', 'Untitled Document')
        document = DocumentApp(title=title, user_id=current_user.id)
        db.session.add(document)
        db.session.commit()

        # Перенаправляем на выбор структуры документа
        return redirect(url_for('documents.select_structure', document_id=document.id))

    return render_template('documents/create_new.html', title='Новый документ')


@documents_bp.route('/<int:document_id>/edit')
@login_required
def edit(document_id):
    document = DocumentApp.query.get_or_404(document_id)

    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)

    # Если у документа есть шаблон, перенаправляем на структурированный редактор
    if document.template_id:
        return redirect(url_for('documents.edit_structured', document_id=document_id))

    # Если у документа нет шаблона, перенаправляем на выбор структуры
    return redirect(url_for('documents.select_structure', document_id=document_id))


@documents_bp.route('/<int:document_id>/update', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document updated')
def update(document_id):
    document = DocumentApp.query.get_or_404(document_id)

    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)

    # Получаем данные из формы или JSON
    if request.is_json:
        data = request.get_json()
        title = data.get('title')
    else:
        title = request.form.get('title')

    if title:
        document.title = title
        document.updated_at = datetime.utcnow()
        db.session.commit()

    return jsonify({'success': True})


@documents_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Document deleted')
def delete(document_id):
    document = DocumentApp.query.get_or_404(document_id)

    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)

    # Удаляем документ
    db.session.delete(document)
    db.session.commit()

    flash('Документ успешно удален', 'success')
    return redirect(url_for('documents.index'))


@documents_bp.route('/blocks/<int:block_id>', methods=['GET'])
@login_required
def get_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)

    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)

    return jsonify({
        'id': block.id,
        'document_id': block.document_id,
        'block_type': block.block_type,
        'content': block.content,
        'order': block.order
    })


@documents_bp.route('/blocks/<int:block_id>', methods=['PUT'])
@login_required
@log_activity(level='INFO', message='Block updated')
def update_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)

    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)

    data = request.get_json()

    if 'content' in data:
        block.content = data['content']

    if 'block_type' in data:
        block.block_type = data['block_type']

    if 'order' in data:
        block.order = data['order']

    block.updated_at = datetime.utcnow()
    block.document.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({'success': True})


@documents_bp.route('/documents/<int:document_id>/blocks', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Block created')
def create_block(document_id):
    document = DocumentApp.query.get_or_404(document_id)

    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)

    data = request.get_json()

    # Get the highest order value
    max_order = db.session.query(db.func.max(DocumentBlock.order)).filter_by(document_id=document_id).scalar() or 0

    block = DocumentBlock(
        document_id=document_id,
        block_type=data.get('block_type', 'paragraph'),
        content=data.get('content', ''),
        order=max_order + 1
    )

    db.session.add(block)
    db.session.commit()

    return jsonify({
        'id': block.id,
        'document_id': block.document_id,
        'block_type': block.block_type,
        'content': block.content,
        'order': block.order
    })


@documents_bp.route('/blocks/<int:block_id>', methods=['DELETE'])
@login_required
@log_activity(level='INFO', message='Block deleted')
def delete_block(block_id):
    block = DocumentBlock.query.get_or_404(block_id)

    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)

    document_id = block.document_id

    db.session.delete(block)

    # Update order of remaining blocks
    blocks = DocumentBlock.query.filter_by(document_id=document_id).filter(DocumentBlock.order > block.order).all()
    for b in blocks:
        b.order -= 1

    db.session.commit()

    return jsonify({'success': True})


@documents_bp.route('/blocks/<int:block_id>/recommendations', methods=['GET'])
@login_required
def get_recommendations(block_id):
    block = DocumentBlock.query.get_or_404(block_id)

    # Check if the current user is the owner of the document
    if block.document.user_id != current_user.id:
        abort(403)

    recommendations = block.recommendations.all()

    result = []
    for rec in recommendations:
        result.append({
            'id': rec.id,
            'start_char': rec.start_char,
            'end_char': rec.end_char,
            'original_text': rec.original_text,
            'suggestion': rec.suggestion,
            'explanation': rec.explanation,
            'type_of_error': rec.type_of_error,
            'ai_provider': rec.ai_provider,
            'status': rec.status
        })

    return jsonify(result)


@documents_bp.route('/recommendations/<int:recommendation_id>', methods=['PUT'])
@login_required
@log_activity(level='INFO', message='Recommendation status updated')
def update_recommendation(recommendation_id):
    recommendation = Recommendation.query.get_or_404(recommendation_id)

    # Check if the current user is the owner of the document
    if recommendation.block.document.user_id != current_user.id:
        abort(403)

    data = request.get_json()

    if 'status' in data:
        recommendation.status = data['status']

    db.session.commit()

    return jsonify({'success': True})


@documents_bp.route('/<int:document_id>/export/<format>', methods=['GET'])
@login_required
@log_activity(level='INFO', message='Document exported')
def export_document(document_id, format):
    from ..services.export_service import export_to_docx, export_to_pdf

    document = DocumentApp.query.get_or_404(document_id)

    # Check if the current user is the owner
    if document.user_id != current_user.id:
        abort(403)

    if format == 'docx':
        file_path = export_to_docx(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.docx")
    elif format == 'pdf':
        file_path = export_to_pdf(document_id)
        return send_file(file_path, as_attachment=True, download_name=f"{document.title}.pdf")
    else:
        abort(400, description="Unsupported format")


@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@log_activity(level='INFO', message='Document uploaded')
def upload_document():
    """Загрузка существующего документа"""
    if request.method == 'POST':
        if 'document' not in request.files and 'text_content' not in request.form:
            flash('Не выбран файл или не введен текст', 'error')
            return redirect(request.url)

        title = request.form.get('title', 'Загруженный документ')

        # Создаем новый документ
        document = DocumentApp(title=title, user_id=current_user.id)
        db.session.add(document)
        db.session.commit()

        if 'document' in request.files and request.files['document'].filename:
            file = request.files['document']

            # Сохраняем файл временно
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Здесь будет логика обработки файла и разбиения на блоки
            # Пока просто создаем один блок с содержимым файла
            content = "Содержимое загруженного файла"

            # Если это docx файл, можно использовать python-docx для извлечения текста
            if filename.endswith('.docx'):
                try:
                    doc = Document(file_path)
                    content = '\n'.join([para.text for para in doc.paragraphs])
                except Exception as e:
                    current_app.logger.error(f"Error parsing docx: {str(e)}")

            # Если это txt файл
            elif filename.endswith('.txt'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    current_app.logger.error(f"Error reading txt: {str(e)}")

            # Удаляем временный файл
            os.remove(file_path)

        elif 'text_content' in request.form:
            content = request.form['text_content']
        else:
            content = ""

        # Создаем блок с содержимым
        block = DocumentBlock(
            document_id=document.id,
            block_type='paragraph',
            content=content,
            order=1
        )
        db.session.add(block)
        db.session.commit()

        # Перенаправляем на выбор структуры документа
        return redirect(url_for('documents.select_structure', document_id=document.id))

    return render_template('documents/upload.html', title='Загрузка документа')


@documents_bp.route('/<int:document_id>/select-structure')
@login_required
def select_structure(document_id):
    """Выбор структуры документа"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    templates = DocumentTemplate.query.all()

    return render_template('documents/select_structure.html',
                           title='Выбор структуры',
                           document=document,
                           templates=templates)


@documents_bp.route('/<int:document_id>/apply-template/<int:template_id>', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Template applied to document')
def apply_template(document_id, template_id):
    """Применение шаблона к документу"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    template = DocumentTemplate.query.get_or_404(template_id)

    # Применяем шаблон к документу
    document.template_id = template.id
    db.session.commit()

    # Создаем секции документа на основе шаблона
    for section_template in template.sections.order_by(DocumentSection.order).all():
        section_content = DocumentSectionContent(
            document_id=document.id,
            section_id=section_template.id,
            content='',
            form_data={}
        )
        db.session.add(section_content)

    db.session.commit()

    # Перенаправляем на редактор документа
    return redirect(url_for('documents.edit_structured', document_id=document.id))


@documents_bp.route('/<int:document_id>/structured-edit')
@login_required
def edit_structured(document_id):
    """Редактор структурированного документа"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    # Если у документа нет шаблона, перенаправляем на выбор структуры
    if not document.template_id:
        return redirect(url_for('documents.select_structure', document_id=document.id))

    # Получаем все секции документа
    sections = db.session.query(
        DocumentSection, DocumentSectionContent
    ).join(
        DocumentSectionContent,
        DocumentSection.id == DocumentSectionContent.section_id
    ).filter(
        DocumentSectionContent.document_id == document.id
    ).order_by(
        DocumentSection.order
    ).all()

    return render_template('documents/structured_editor.html',
                           title=document.title,
                           document=document,
                           sections=sections)


@documents_bp.route('/<int:document_id>/section/<int:section_id>/edit')
@login_required
def edit_section(document_id, section_id):
    """Редактирование отдельной секции документа"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    section = DocumentSection.query.get_or_404(section_id)
    section_content = DocumentSectionContent.query.filter_by(
        document_id=document_id,
        section_id=section_id
    ).first_or_404()

    # Если секция заполняется через форму
    if section.is_form_based:
        return render_template('documents/section_form.html',
                               title=f"{document.title} - {section.name}",
                               document=document,
                               section=section,
                               section_content=section_content)

    # Если секция редактируется в редакторе
    return render_template('documents/section_editor.html',
                           title=f"{document.title} - {section.name}",
                           document=document,
                           section=section,
                           section_content=section_content)


@documents_bp.route('/<int:document_id>/section/<int:section_id>/update', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Section updated')
def update_section(document_id, section_id):
    """Обновление содержимого секции"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    section = DocumentSection.query.get_or_404(section_id)
    section_content = DocumentSectionContent.query.filter_by(
        document_id=document_id,
        section_id=section_id
    ).first_or_404()

    # Обновляем содержимое в зависимости от типа секции
    if section.is_form_based:
        # Для секций на основе форм сохраняем данные формы
        form_data = {}
        for field in request.form:
            if field != 'csrf_token':
                form_data[field] = request.form[field]

        section_content.form_data = form_data
        # Генерируем текстовое представление из данных формы
        # Это упрощенный пример, в реальности нужна более сложная логика
        section_content.content = json.dumps(form_data, ensure_ascii=False)
    else:
        # Для секций с редактором сохраняем HTML-содержимое
        section_content.content = request.form.get('content', '')

    section_content.updated_at = datetime.utcnow()
    document.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})


@documents_bp.route('/<int:document_id>/preview')
@login_required
def preview_document(document_id):
    """Предпросмотр документа"""
    document = DocumentApp.query.get_or_404(document_id)

    # Проверяем, что текущий пользователь является владельцем
    if document.user_id != current_user.id:
        abort(403)

    # Получаем все секции документа
    sections = db.session.query(
        DocumentSection, DocumentSectionContent
    ).join(
        DocumentSectionContent,
        DocumentSection.id == DocumentSectionContent.section_id
    ).filter(
        DocumentSectionContent.document_id == document.id
    ).order_by(
        DocumentSection.order
    ).all()

    return render_template('documents/preview.html',
                           title=f"Предпросмотр - {document.title}",
                           document=document,
                           sections=sections)


@documents_bp.route('/title-form')
@login_required
def title_form():
    """Страница с формой для создания титульного листа"""
    return render_template('documents/title_form.html', title='Создание титульного листа')


@documents_bp.route('/generate-title', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Title page generated')
def generate_title():
    """Генерация титульного листа"""
    data = request.get_json()

    # Здесь будет логика генерации титульного листа
    # Пока просто создаем документ с заголовком

    document = DocumentApp(title=data.get('work-theme', 'Новый документ'), user_id=current_user.id)
    db.session.add(document)
    db.session.commit()

    # Создаем блок с содержимым
    content = f"""
    <h1 style="text-align: center;">{data.get('university-info', '')}</h1>
    <h2 style="text-align: center;">{data.get('work-type', '')}</h2>
    <h3 style="text-align: center;">по дисциплине "{data.get('work-subject', '')}"</h3>
    <h2 style="text-align: center;">на тему: "{data.get('work-theme', '')}"</h2>
    <p style="text-align: right;">Выполнил: {data.get('fullname', '')}</p>
    <p style="text-align: right;">Группа: {data.get('group', '')}</p>
    <p style="text-align: right;">Проверил: {data.get('educator', '')}</p>
    <p style="text-align: center; margin-top: 50px;">{data.get('city', '')}</p>
    """

    block = DocumentBlock(
        document_id=document.id,
        block_type='paragraph',
        content=content,
        order=1
    )
    db.session.add(block)
    db.session.commit()

    # Перенаправляем на редактирование документа
    return jsonify({'success': True, 'document_id': document.id})

