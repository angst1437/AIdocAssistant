import asyncio
import logging
import sys

from os import getenv, makedirs, path, remove
from docx import Document

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv

from logic import builder, datatypes



load_dotenv()
TOKEN = getenv('TOKEN')
DOWNLOAD_PATH = "../files"
OUTPUT = "рекомендованные исправления.docx"


class TgBot(Bot):
    dp = Dispatcher()

    def __init__(self, output, path, token):
        """Дополняет init родительского класса, добавляя поля класса OUTPUT и DOWNLOAD_PATH"""
        super().__init__(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)) # вызов родительского init
        self.OUTPUT = output
        self.DOWNLOAD_PATH = path


    @dp.message(CommandStart())
    async def start_command(message: Message) -> None:
        """Приветствие, вызываемое командой /start"""
        await message.answer('Привет! Я бот который поможет тебе с твоей работой. '
                             'Введи команду /create чтобы начать создавать документ.')

    @dp.message(commands=['create'])
    async def create_command( message: Message) -> None:

    def get_dp(self):
        """
        Возвращает диспетчера, созданного внутри класса
        ВОЗМОЖНО костыль
        """
        return self.dp



async def main() -> None:
    bot = TgBot(token=TOKEN, path=DOWNLOAD_PATH, output=OUTPUT)
    dp = bot.get_dp()
    dp.message(F.document)(bot.handle_document) # используется здесь вместо декоратора, т.к. с декоратором невозможно использовать self
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())