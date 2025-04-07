from web.app import db
from web.app.models import TextRecommendation, DocumentApp
from web.app.services.document_service import DocumentService


class RecommendationService:
    @staticmethod
    def create_recommendation(document_id, section_id, user_id, start_char, end_char, original_text, suggestion,
                              explanation, type_of_error, ai_provider):
        """
        Создает новую рекомендацию

        Args:
            document_id (int): ID документа
            section_id (int): ID секции
            user_id (int): ID пользователя
            start_char (int): Начальная позиция проблемного текста
            end_char (int): Конечная позиция проблемного текста
            original_text (str): Проблемный текст
            suggestion (str): Рекомендуемая замена
            explanation (str): Объяснение проблемы
            type_of_error (str): Тип проблемы
            ai_provider (str): Провайдер ИИ

        Returns:
            TextRecommendation: Созданная рекомендация или None, если пользователь не имеет доступа к документу
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return None

        recommendation = TextRecommendation(
            document_id=document_id,
            section_id=section_id,
            start_char=start_char,
            end_char=end_char,
            original_text=original_text,
            suggestion=suggestion,
            explanation=explanation,
            type_of_error=type_of_error,
            ai_provider=ai_provider,
            status='pending'
        )

        db.session.add(recommendation)
        db.session.commit()
        return recommendation

    @staticmethod
    def get_recommendations(document_id, section_id, user_id):
        """
        Получает рекомендации для секции документа

        Args:
            document_id (int): ID документа
            section_id (int): ID секции
            user_id (int): ID пользователя

        Returns:
            list: Список рекомендаций или None, если пользователь не имеет доступа к документу
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return None

        recommendations = TextRecommendation.query.filter_by(
            document_id=document_id,
            section_id=section_id
        ).all()

        return recommendations

    @staticmethod
    def update_recommendation_status(recommendation_id, user_id, status):
        """
        Обновляет статус рекомендации

        Args:
            recommendation_id (int): ID рекомендации
            user_id (int): ID пользователя
            status (str): Новый статус

        Returns:
            bool: True, если статус успешно обновлен, иначе False
        """
        recommendation = TextRecommendation.query.get(recommendation_id)
        if not recommendation:
            return False

        document = DocumentService.get_document(recommendation.document_id, user_id)
        if not document:
            return False

        recommendation.status = status
        db.session.commit()
        return True

