from flask import current_app
from web.app import db
from web.app.models import DocumentApp, DocumentSection, DocumentSectionContent, TextRecommendation
import os
from datetime import datetime


class DocumentService:
    @staticmethod
    def create_document(title, user_id, template_id=None):
        """
        Создает новый документ

        Args:
            title (str): Название документа
            user_id (int): ID пользователя
            template_id (int, optional): ID шаблона

        Returns:
            DocumentApp: Созданный документ
        """
        document = DocumentApp(
            title=title,
            user_id=user_id,
            template_id=template_id
        )
        db.session.add(document)
        db.session.commit()
        return document

    @staticmethod
    def get_document(document_id, user_id=None):
        """
        Получает документ по ID

        Args:
            document_id (int): ID документа
            user_id (int, optional): ID пользователя для проверки доступа

        Returns:
            DocumentApp: Документ или None, если документ не найден или пользователь не имеет доступа
        """
        document = DocumentApp.query.get(document_id)
        if not document:
            return None

        if user_id is not None and document.user_id != user_id:
            return None

        return document

    @staticmethod
    def update_document(document_id, user_id, title=None):
        """
        Обновляет документ

        Args:
            document_id (int): ID документа
            user_id (int): ID пользователя
            title (str, optional): Новое название документа

        Returns:
            bool: True, если документ успешно обновлен, иначе False
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return False

        if title:
            document.title = title

        document.updated_at = datetime.utcnow()
        db.session.commit()
        return True

    @staticmethod
    def delete_document(document_id, user_id):
        """
        Удаляет документ

        Args:
            document_id (int): ID документа
            user_id (int): ID пользователя

        Returns:
            bool: True, если документ успешно удален, иначе False
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return False

        db.session.delete(document)
        db.session.commit()
        return True

    @staticmethod
    def get_section_content(document_id, section_id, user_id=None):
        """
        Получает содержимое секции документа

        Args:
            document_id (int): ID документа
            section_id (int): ID секции
            user_id (int, optional): ID пользователя для проверки доступа

        Returns:
            DocumentSectionContent: Содержимое секции или None
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return None

        section_content = DocumentSectionContent.query.filter_by(
            document_id=document_id,
            section_id=section_id
        ).first()

        return section_content

    @staticmethod
    def update_section_content(document_id, section_id, user_id, content=None, form_data=None):
        """
        Обновляет содержимое секции документа

        Args:
            document_id (int): ID документа
            section_id (int): ID секции
            user_id (int): ID пользователя
            content (str, optional): Новое содержимое секции
            form_data (dict, optional): Новые данные формы

        Returns:
            bool: True, если содержимое успешно обновлено, иначе False
        """
        document = DocumentService.get_document(document_id, user_id)
        if not document:
            return False

        section_content = DocumentSectionContent.query.filter_by(
            document_id=document_id,
            section_id=section_id
        ).first()

        if not section_content:
            section_content = DocumentSectionContent(
                document_id=document_id,
                section_id=section_id,
                content='',
                form_data={}
            )
            db.session.add(section_content)

        if content is not None:
            section_content.content = content

        if form_data is not None:
            section_content.form_data = form_data

        section_content.updated_at = datetime.utcnow()
        document.updated_at = datetime.utcnow()
        db.session.commit()
        return True

