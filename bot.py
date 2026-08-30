import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from downloader import download_video, extract_url
from mediatools import parse_time_range, rename, to_mp3, trim

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
router = Router()

TELEGRAM_UPLOAD_LIMIT = 50 * 1024 * 1024


class Form(StatesGroup):
    trimming = State()
    renaming = State()


def actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎵 В MP3", callback_data="to_mp3"),
                InlineKeyboardButton(text="✂️ Обрезать", callback_data="trim"),
            ],
            [InlineKeyboardButton(text="✏️ Переименовать", callback_data="rename")],
        ]
    )


async def send_result(message: Message, path: Path):
    if path.stat().st_size > TELEGRAM_UPLOAD_LIMIT:
        await message.answer(
            "Готово, но файл больше 50 МБ — Telegram не даст боту его отправить. "
            "Попробуйте обрезать или сохранить в mp3, чтобы уменьшить размер."
        )
        return
    file = FSInputFile(path)
    if path.suffix.lower() == ".mp3":
        await message.answer_audio(file, reply_markup=actions_keyboard())
    else:
        await message.answer_video(file, reply_markup=actions_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Пришли мне ссылку на видео из YouTube, TikTok или Instagram — я его скачаю.\n\n"
        "После скачивания можно:\n"
        "🎵 Превратить в MP3\n"
        "✂️ Обрезать по времени\n"
        "✏️ Переименовать (артист + название)"
    )


@router.message(F.text.regexp(r"https?://\S+"))
async def handle_link(message: Message, state: FSMContext):
    url = extract_url(message.text)
    status = await message.answer("Скачиваю…")
    try:
        path = await asyncio.to_thread(download_video, url, message.chat.id)
    except Exception as e:
        await status.edit_text(f"Не удалось скачать: {e}")
        return
    await state.update_data(current_file=str(path))
    await status.delete()
    await send_result(message, path)


@router.callback_query(F.data == "to_mp3")
async def cb_to_mp3(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_file")
    if not current:
        await callback.answer("Сначала пришли ссылку на видео.", show_alert=True)
        return
    await callback.answer("Конвертирую…")
    try:
        mp3_path = await asyncio.to_thread(to_mp3, Path(current))
    except Exception as e:
        await callback.message.answer(f"Ошибка конвертации: {e}")
        return
    await state.update_data(current_file=str(mp3_path))
    await send_result(callback.message, mp3_path)


@router.callback_query(F.data == "trim")
async def cb_trim(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("current_file"):
        await callback.answer("Сначала пришли ссылку на видео.", show_alert=True)
        return
    await state.set_state(Form.trimming)
    await callback.answer()
    await callback.message.answer(
        "Пришли диапазон времени в формате `00:10-00:40`", parse_mode="Markdown"
    )


@router.message(Form.trimming)
async def process_trim(message: Message, state: FSMContext):
    time_range = parse_time_range(message.text)
    if not time_range:
        await message.answer("Неверный формат. Пример: `00:10-00:40`", parse_mode="Markdown")
        return
    data = await state.get_data()
    current = Path(data["current_file"])
    status = await message.answer("Обрезаю…")
    try:
        start, end = time_range
        trimmed_path = await asyncio.to_thread(trim, current, start, end)
    except Exception as e:
        await status.edit_text(f"Ошибка обрезки: {e}")
        return
    await state.update_data(current_file=str(trimmed_path))
    await state.set_state(None)
    await status.delete()
    await send_result(message, trimmed_path)


@router.callback_query(F.data == "rename")
async def cb_rename(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("current_file"):
        await callback.answer("Сначала пришли ссылку на видео.", show_alert=True)
        return
    await state.set_state(Form.renaming)
    await callback.answer()
    await callback.message.answer("Пришли артиста и название в формате `Артист - Название`", parse_mode="Markdown")


@router.message(Form.renaming)
async def process_rename(message: Message, state: FSMContext):
    if "-" not in message.text:
        await message.answer("Неверный формат. Пример: `Imagine Dragons - Believer`", parse_mode="Markdown")
        return
    artist, title = (part.strip() for part in message.text.split("-", 1))
    data = await state.get_data()
    current = Path(data["current_file"])
    status = await message.answer("Переименовываю…")
    try:
        renamed_path = await asyncio.to_thread(rename, current, artist, title)
    except Exception as e:
        await status.edit_text(f"Ошибка переименования: {e}")
        return
    await state.update_data(current_file=str(renamed_path))
    await state.set_state(None)
    await status.delete()
    await send_result(message, renamed_path)


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN не задан. Скопируй .env.example в .env и вставь токен.")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
