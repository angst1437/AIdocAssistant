import ollama

from ollama import chat
from ollama import ChatResponse
import logic.LlamaConfig as LlamaConfig


def check_title(text):
    response: ChatResponse = chat(model='qwen2.5', messages=[
      {
        'role': 'system',
        'content': 'Ты персональный помощник, определяющий тип текста. Похож ли следующий текст на титульный лист реферата? Титульный лист должен содержать: учебное заведение, тему, исполнителей, руководителя, город и год. Отвечай только да или нет.',
      },
        {
            'role': 'user',
            'content': text,
        }
    ])
    return response['message']['content'].lower().strip()

def check_main_part(text):
    response: ChatResponse = chat(model='qwen2.5', messages=[
      {
        'role': 'system',
        'content': 'Ты персональный помощник, определяющий тип текста. Похож ли следующий текст на пункт основной части реферата? Отвечай только да или нет.',
      },
        {
            'role': 'user',
            'content': text,
        }
    ])
    return response['message']['content'].lower().strip()

def title_sort(text):
    response: ChatResponse = chat(model='qwen2.5', messages=[
        {
            'role': 'system',
            'content': LlamaConfig.TITLE_SORT_PROMPT
        },
        {
            'role': 'user',
            'content': text,
        }
    ], options={"temperature": 0.1})
    return response['message']['content']