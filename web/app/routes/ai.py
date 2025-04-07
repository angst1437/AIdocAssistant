from flask import Blueprint, request, jsonify, current_app

from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from .. import db
from ..models import DocumentApp, DocumentSection, DocumentSectionContent, TextRecommendation
from ..services.ai_clients import get_ai_client
from ..services.recommendation_service import RecommendationService
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
    section_id = data.get('section_id')
    document_id = data.get('document_id')
    provider = data.get('provider', 'yandex')
    check_type = data.get('check_type', 'all')

    # Проверяем, что секция принадлежит текущему пользователю
    if section_id and document_id:
        section_content = DocumentSectionContent.query.filter_by(
            document_id=document_id,
            section_id=section_id
        ).first_or_404()

        document = DocumentApp.query.get_or_404(document_id)
        if document.user_id != current_user.id:
            abort(403)

    try:
        # Получаем соответствующий AI-клиент
        ai_client = get_ai_client(provider)

        # Анализируем текст
        recommendations = ai_client.analyze_text(text, check_type)

        # Сохраняем рекомендации в базу данных
        saved_recommendations = []
        for rec in recommendations:
            # Создаем новую рекомендацию
            recommendation = RecommendationService.create_recommendation(
                document_id=document_id,
                section_id=section_id,
                user_id=current_user.id,
                start_char=rec.get('start_char', 0),
                end_char=rec.get('end_char', 0),
                original_text=rec.get('original_text', ''),
                suggestion=rec.get('suggestion', ''),
                explanation=rec.get('explanation', ''),
                type_of_error=rec.get('type_of_error', 'unknown'),
                ai_provider=provider
            )

            if recommendation:
                saved_recommendations.append({
                    'id': recommendation.id,
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

        return jsonify(saved_recommendations)

    except Exception as e:
        # Логируем ошибку
        current_app.logger.error(f"AI analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/section/<int:document_id>/<int:section_id>/recommendations', methods=['GET'])
@login_required
def get_section_recommendations(document_id, section_id):
    """Получение рекомендаций для секции документа"""
    recommendations = RecommendationService.get_recommendations(document_id, section_id, current_user.id)
    if recommendations is None:
        abort(403)

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
    data = request.get_json()

    if 'status' not in data:
        abort(400, description="Missing status field")

    success = RecommendationService.update_recommendation_status(
        recommendation_id,
        current_user.id,
        data['status']
    )

    if not success:
        abort(403)

    return jsonify({'success': True})

