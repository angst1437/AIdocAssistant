import requests
import json
from abc import ABC, abstractmethod
from flask import current_app

# System prompt for AI
SYSTEM_PROMPT = """Ты — эксперт по научному стилю и требованиям ГОСТ 7.32-2017 для оформления научно-исследовательских работ. Твоя задача — проверить текст на соответствие требованиям и дать рекомендации по улучшению.

Проверяй следующие аспекты:
1. Научный стиль: отсутствие разговорных выражений, жаргонизмов, эмоционально окрашенных слов.
2. Грамматика и пунктуация: правильность построения предложений, согласование слов, расстановка знаков препинания.
3. Соответствие ГОСТ 7.32-2017: правильное оформление заголовков, таблиц, рисунков, формул, списков литературы.
4. Терминология: корректное использование научных терминов.
5. Логика и структура: связность текста, логичность изложения.

Для каждой найденной проблемы укажи:
- Проблемный фрагмент текста
- Тип проблемы (стиль, грамматика, ГОСТ, терминология, логика)
- Объяснение проблемы
- Ре��омендацию по исправлению

Возвращай результат в формате JSON:
[
  {
    "start_char": <начальная_позиция>,
    "end_char": <конечная_позиция>,
    "original_text": "<проблемный_текст>",
    "suggestion": "<рекомендуемая_замена>",
    "explanation": "<объяснение_проблемы>",
    "type_of_error": "<тип_проблемы>"
  },
  ...
]

Если ошибок нет, верни пустой список []."""


class AIClient(ABC):
    """Base abstract class for AI clients"""

    @abstractmethod
    def analyze_text(self, text, check_type=None):
        """
        Analyze text and return recommendations

        Args:
            text (str): Text to analyze
            check_type (str, optional): Type of check to perform (style, grammar, gost, etc.)

        Returns:
            list: List of recommendations
        """
        pass


class YandexGPTClient(AIClient):
    """Client for YandexGPT API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('YANDEX_GPT_API_KEY')
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.model = "yandexgpt"

    def analyze_text(self, text, check_type=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }

        prompt = f"{SYSTEM_PROMPT}\n\nТекст для проверки:\n{text}"
        if check_type:
            prompt += f"\n\nОсобое внимание обрати на аспект: {check_type}"

        data = {
            "modelUri": f"gpt://{self.model}/latest",
            "completionOptions": {
                "temperature": 0.1,
                "maxTokens": 1500
            },
            "messages": [
                {
                    "role": "system",
                    "text": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            # Extract the response text
            response_text = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text', '[]')

            # Parse JSON from the response
            try:
                recommendations = json.loads(response_text)
                return recommendations
            except json.JSONDecodeError:
                current_app.logger.error(f"Failed to parse JSON from YandexGPT response: {response_text}")
                return []

        except Exception as e:
            current_app.logger.error(f"YandexGPT API error: {str(e)}")
            return []


class GigaChatClient(AIClient):
    """Client for GigaChat API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('GIGACHAT_API_KEY')
        self.api_url = "https://gigachat-api.ru/v1/chat/completions"
        self.model = "GigaChat"

    def analyze_text(self, text, check_type=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"{SYSTEM_PROMPT}\n\nТекст для проверки:\n{text}"
        if check_type:
            prompt += f"\n\nОсобое внимание обрати на аспект: {check_type}"

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1500
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            # Extract the response text
            response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '[]')

            # Parse JSON from the response
            try:
                recommendations = json.loads(response_text)
                return recommendations
            except json.JSONDecodeError:
                current_app.logger.error(f"Failed to parse JSON from GigaChat response: {response_text}")
                return []

        except Exception as e:
            current_app.logger.error(f"GigaChat API error: {str(e)}")
            return []


class GeminiClient(AIClient):
    """Client for Google Gemini API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

    def analyze_text(self, text, check_type=None):
        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"{SYSTEM_PROMPT}\n\nТекст для проверки:\n{text}"
        if check_type:
            prompt += f"\n\nОсобое внимание обрати на аспект: {check_type}"

        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1500
            }
        }

        try:
            response = requests.post(f"{self.api_url}?key={self.api_key}", headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            # Extract the response text
            response_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')

            # Parse JSON from the response
            try:
                recommendations = json.loads(response_text)
                return recommendations
            except json.JSONDecodeError:
                current_app.logger.error(f"Failed to parse JSON from Gemini response: {response_text}")
                return []

        except Exception as e:
            current_app.logger.error(f"Gemini API error: {str(e)}")
            return []


def get_ai_client(provider='yandex'):
    """Factory function to get the appropriate AI client"""
    if provider == 'yandex':
        return YandexGPTClient()
    elif provider == 'gigachat':
        return GigaChatClient()
    elif provider == 'gemini':
        return GeminiClient()
    else:
        raise ValueError(f"Unknown AI provider: {provider}")

