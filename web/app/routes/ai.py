from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from .. import db
from ..models import DocumentBlock, Recommendation, LogEntry, DocumentApp, DocumentSectionContent, TextRecommendation
from ..services.ai_clients import get_ai_client
from ..utils.decorators import log_activity

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/analyze', methods=['POST'])
@login_required
@log_activity(level='INFO', message='AI analysis requested')
def analyze_text():
    data = request.get_json()

    if not data or 'text' not in data:
        abort(400, description="Missing required fields")

    text = data['text']
    block_id = data.get('block_id')
    section_id = data.get('section_id')
    document_id = data.get('document_id')
    provider = data.get('provider', 'yandex')
    check_type = data.get('check_type', 'all')

    # Проверяем, что блок или секция принадлежат текущему пользователю
    if block_id:
        block = DocumentBlock.query.get_or_404(block_id)
        if block.document.user_id != current_user.id:
            abort(403)
    elif section_id and document_id:
        section_content = DocumentSectionContent.query.filter_by(
            document_id=document_id,
            section_id=section_id
        ).first_or_404()
        if section_content.document.user_id != current_user.id:
            abort(403)

    try:
        # Получаем соответствующий AI-клиент
        ai_client = get_ai_client(provider)

        # Анализируем текст
        recommendations = ai_client.analyze_text(text, check_type)

        # Сохраняем рекомендации в базу данных
        saved_recommendations = []
        for rec in recommendations:
            if block_id:
                # Для старого формата с блоками
                recommendation = Recommendation(
                    block_id=block_id,
                    start_char=rec.get('start_char', 0),
                    end_char=rec.get('end_char', 0),
                    original_text=rec.get('original_text', ''),
                    suggestion=rec.get('suggestion', ''),
                    explanation=rec.get('explanation', ''),
                    type_of_error=rec.get('type_of_error', 'unknown'),
                    ai_provider=provider,
                    status='pending'
                )
            else:
                # Для нового формата с секциями
                # Создаем новую модель TextRecommendation
                recommendation = TextRecommendation(
                    document_id=document_id,
                    section_id=section_id,
                    start_char=rec.get('start_char', 0),
                    end_char=rec.get('end_char', 0),
                    original_text=rec.get('original_text', ''),
                    suggestion=rec.get('suggestion', ''),
                    explanation=rec.get('explanation', ''),
                    type_of_error=rec.get('type_of_error', 'unknown'),
                    ai_provider=provider,
                    status='pending'
                )

            db.session.add(recommendation)
            saved_recommendations.append({
                'id': None,  # Будет обновлено после коммита
                'start_char': recommendation.start_char,
                'end_char': recommendation.end_char,
                'original_text': recommendation.original_text,
                'suggestion': recommendation.suggestion,
                'explanation': recommendation.explanation,
                'type_of_error': recommendation.type_of_error,
                'ai_provider': recommendation.ai_provider,
                'status': recommendation.status,
                'variants': rec.get('variants', [])  # Варианты исправления
            })

        db.session.commit()

        # Обновляем ID после коммита
        for i, rec in enumerate(saved_recommendations):
            if block_id:
                rec['id'] = recommendations[i].id
            else:
                rec['id'] = recommendations[i].id

        return jsonify(saved_recommendations)

    except Exception as e:
        # Логируем ошибку
        error_log = LogEntry(
            level='ERROR',
            message=f"AI analysis error: {str(e)}",
            user_id=current_user.id,
            request_url=request.path,
            ip_address=request.remote_addr
        )
        db.session.add(error_log)
        db.session.commit()

        current_app.logger.error(f"AI analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/section/<int:document_id>/<int:section_id>/recommendations', methods=['GET'])
@login_required
def get_section_recommendations(document_id, section_id):
    """Получение рекомендаций для секции документа"""
    # Проверяем, что документ принадлежит текущему пользователю
    document = DocumentApp.query.get_or_404(document_id)
    if document.user_id != current_user.id:
        abort(403)

    # Получаем рекомендации для секции
    recommendations = TextRecommendation.query.filter_by(
        document_id=document_id,
        section_id=section_id
    ).all()

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


@ai_bp.route('/recommendations/<int:recommendation_id>', methods=['PUT'])
@login_required
@log_activity(level='INFO', message='Recommendation status updated')
def update_recommendation_status(recommendation_id):
    """Обновление статуса рекомендации"""
    # Проверяем, существует ли рекомендация для блока
    recommendation = Recommendation.query.get(recommendation_id)

    if recommendation:
        # Проверяем, что блок принадлежит текущему пользователю
        if recommendation.block.document.user_id != current_user.id:
            abort(403)
    else:
        # Проверяем, существует ли рекомендация для секции
        recommendation = TextRecommendation.query.get_or_404(recommendation_id)

        # Проверяем, что документ принадлежит текущему пользователю
        document = DocumentApp.query.get(recommendation.document_id)
        if document.user_id != current_user.id:
            abort(403)

    data = request.get_json()

    if 'status' in data:
        recommendation.status = data['status']

    db.session.commit()

    return jsonify({'success': True})

