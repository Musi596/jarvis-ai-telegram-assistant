import asyncio
import io
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ai import ask_ai, transcribe
from config import BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

history: dict[int, list[dict]] = {}
MAX_MESSAGES = 10
TELEGRAM_LIMIT = 4000 


def remember(user_id: int, role: str, text: str):
    history.setdefault(user_id, []).append({"role": role, "content": text})
    history[user_id] = history[user_id][-MAX_MESSAGES:]


async def reply_with_ai(message: Message, user_text: str):
    user_id = message.from_user.id
    remember(user_id, "user", user_text)

    try:
        answer = await ask_ai(history[user_id])
    except Exception as error:
        logging.error(f"Ошибка AI: {error}")
        await message.answer("AI сейчас не отвечает 😔 Попробуй ещё раз.")
        return

    remember(user_id, "assistant", answer)
    await message.answer(answer[:TELEGRAM_LIMIT], parse_mode="Markdown")

@dp.message(CommandStart())
async def start_handler(message: Message):
    history.pop(message.from_user.id, None)
    await message.answer(
        "*Привет! 👋 Я твой AI-помощник.*\n\n"
        "*✍️ Напиши мне текстовое сообщение или*\n"
        "*🎤 отправь голосовое сообщение.*\n\n"
        "`/clear` — забыть наш разговор\n"
        "`/help` — как мной пользоваться",
        parse_mode="Markdown"
    )


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Я умею *отвечать на вопросы*, *объяснять темы*, *переводить* и *писать тексты*.\n"
        "Я помню несколько последних сообщений, поэтому можно задавать уточняющие вопросы.\n"
        "Используй `/clear`, чтобы начать новый разговор.",
        parse_mode="Markdown"
    )


@dp.message(Command("clear"))
async def clear_handler(message: Message):
    history.pop(message.from_user.id, None)
    await message.answer("*Память очищена* 🧹 *Начнём заново.*", parse_mode="Markdown")

@dp.message(F.voice | F.audio)
async def voice_handler(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")

    file_object = message.voice or message.audio

    try:
        buffer = io.BytesIO()
        await bot.download(file_object, destination=buffer)
        user_text = await transcribe(buffer.getvalue())
    except Exception as error:
        logging.error(f"Ошибка аудио: {error}")
        await message.answer("Не получилось прочитать это аудио 😔 Попробуй отправить более короткое.")
        return

    if not user_text:
        await message.answer("Я не услышал слов. Попробуй ещё раз 🎤")
        return

    await message.answer(f"🎧 *Я услышал:* *{user_text}*", parse_mode="Markdown")
    await reply_with_ai(message, user_text)

@dp.message(F.text)
async def text_handler(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    await reply_with_ai(message, message.text)

@dp.message()
async def other_handler(message: Message):
    await message.answer("*Пока я понимаю только* текстовые и голосовые сообщения 🙂", parse_mode="Markdown")
async def main():
    logging.info("Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
