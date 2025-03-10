import asyncio
import logging
import sys

from os import getenv, makedirs, path
from docx import Document

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

from analys import analysis_conclusion, analysis_introduction, analysis_introduction_and_conclusion,analysis_literList
from CheckStructure import check_sections_in_docx, write_sections_to_docx


load_dotenv()
TOKEN = getenv('TOKEN')
DOWNLOAD_PATH = "files"
OUTPUT = "рекомендованные исправления.docx"

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

section_keywords = ['список исполнителей','реферат',
                    'содержание', 'термины и определения', 'перечень сокращений и обозначений',
                    'введение', 'заключение',
                    'список использованных источников','приложения',
                    ]

@dp.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer('Привет! Я бот который поможет тебе с твоей работой. '
                         'Отправь мне твою работу и я проверю её на соответствие ГОСТу')

@dp.message(F.document)
async def handle_document(message: Message) -> None:
    file_id = message.document.file_id
    file_name = message.document.file_name

    makedirs(DOWNLOAD_PATH, exist_ok=True)

    # try:
    file = await bot.get_file(file_id)
    file_tg_path = file.file_path
    file_path = path.join(DOWNLOAD_PATH, file_name)

    await bot.download_file(file_tg_path, file_path)
    await message.answer(f"Файл {file_name} успешно скачан! Начинаю анализ")

    logging.info(file_path)
    sections = check_sections_in_docx(file_path, section_keywords)
    write_sections_to_docx(OUTPUT, sections, file_path)
    new_doc = Document(OUTPUT)


    if sections.get('введение'):
        introduction = analysis_introduction(file_path, 'введение')
        new_doc.add_paragraph(introduction)
    if sections.get('заключение'):
        conclusion = analysis_conclusion(file_path, 'заключение')
        new_doc.add_paragraph(conclusion)
    if sections.get('введение') and sections.get('заключение'):
        introduction_and_conclusion = analysis_introduction_and_conclusion(file_path, 'введение', 'заключение')
        new_doc.add_paragraph(introduction_and_conclusion)
    if sections.get('список использованных источников'):
        liter_list = analysis_literList(file_path, 'список использованных источников')
        new_doc.add_paragraph(liter_list)
    new_doc.save(OUTPUT)
    doc = FSInputFile(OUTPUT)
    await message.answer_document(doc)

    # except Exception as e:
    #     await message.answer("Произошла ошибка при скачивании файла.")



async def main() -> None:

    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())