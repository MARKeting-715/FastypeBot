import asyncio
import logging
import sys
from itertools import zip_longest
from time import time

from aiogram import Bot, Dispatcher, F, exceptions
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (Message, CallbackQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import API_KEY
from ai_models.llama import llama
from ai_models.gemini import gemini
from ai_models.deepseek import deepseek
from ai_models.mistral import mistral
from ai_models.qwen import qwen

# конфиггг
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_KEY)
dp = Dispatcher()

models = {
    "gemini": gemini,
    "llama": llama,
    "deepseek": deepseek,
    "mistral": mistral,
    "qwen": qwen
}

class States(StatesGroup):
    pick_model = State()
    awaiting_text = State()
    awaiting_input = State()

# Помогатор
async def sentence_checking(reference: str, user_input: str) -> tuple[str, int]:
    errors = 0
    output = []
    for ref_word, usr_word in zip_longest(reference.split(), user_input.split(), fillvalue=""):
        word_res = []
        for r_char, u_char in zip_longest(ref_word, usr_word, fillvalue=""):
            if r_char == u_char or (r_char in "её" and u_char in "её"):
                word_res.append(r_char)
            else:
                word_res.append(f"<b><u>{r_char}</u></b>")
                errors += 1
        output.append("".join(word_res))
    return " ".join(output), errors


def build_start_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Начать", callback_data="start_game"))
    builder.add(InlineKeyboardButton(text="Выбрать модель", callback_data="change_model"))
    return builder.as_markup()

def build_model_markup(current: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in models.keys():
        label = f"{key} ✅" if key == current else key
        builder.add(InlineKeyboardButton(text=label, callback_data=key))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.adjust(1).as_markup()

def build_endgame_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Продолжить", callback_data="start_game"),
        InlineKeyboardButton(text="Назад", callback_data="back")
    )
    return builder.as_markup()

# Error handler
@dp.errors()
async def global_error_handler(update, exception: Exception):
    logger.error(f"Exception in update {update}: {exception}")
    if isinstance(exception, exceptions.BotBlocked):
        logger.warning("Bot is blocked by user.")
        return True
    return False

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logger.debug(f"/start from {message.from_user.id}")
    try:
        await state.clear()
        await message.delete()
    except exceptions.TelegramAPIError as e:
        logger.warning(f"Failed to delete start message: {e}")
    await message.answer(
        "Привет, это fastype бот, он поможет вам в тренировке слепой печати.",
        reply_markup=build_start_markup()
    )
    await state.set_state(States.pick_model)

@dp.callback_query(F.data.in_(models.keys() | {"change_model"}))
async def on_change_model(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data() or {}
    current = data.get("model", "gemini")
    if callback.data in models:
        await state.update_data(model=callback.data)
        current = callback.data
n    await callback.message.edit_text(
        "Выберите модель",
        reply_markup=build_model_markup(current)
    )
    await callback.answer()

@dp.callback_query(F.data == "start_game")
async def on_start_game(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Starting game for {callback.from_user.id}")
    await callback.answer("Генерация текста...", show_alert=False)
    data = await state.get_data() or {}
    model_key = data.get("model", "gemini")
    gen_func = models.get(model_key, gemini)
    try:
        text = await gen_func()
    except Exception as e:
        logger.error(f"AI model generation failed: {e}")
        text = "Не удалось получить ответ, смените модель"
    await state.update_data(text=text, start_time=time())
    try:
        await callback.message.edit_text(
            text,
            reply_markup=build_endgame_markup()
        )
        await state.set_state(States.awaiting_input)
    except exceptions.TelegramAPIError as e:
        logger.error(f"Failed to edit message: {e}")
    await callback.answer()

@dp.message(States.awaiting_input)
async def on_user_input(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("text", "")
    elapsed = time() - data.get("start_time", time())
    user_text = message.text
    await message.delete()
    checked, errors = await sentence_checking(text, user_text)
    words = len(text.split())
    speed = round(words / (elapsed / 60), 1)
    total_chars = len(text.replace(" ", ""))
    accuracy = round((1 - errors / total_chars) * 100, 1) if total_chars else 0
    result_msg = (
        f"{checked}\n\n{user_text}\n\n"
        f"Вы справились за {round(elapsed, 2)} секунд\n"
        f"Скорость: {speed} слов/мин\n"
        f"Аккуратность: {accuracy}%"
    )
    if text == "Не удалось получить ответ, смените модель":
        result_msg += "\n\n*пасхалка найдена!*"
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=result_msg,
            reply_markup=build_endgame_markup(),
            parse_mode="HTML"
        )
    except exceptions.TelegramAPIError as e:
        logger.error(f"Failed to send result: {e}")
    await state.set_state(States.pick_model)

@dp.callback_query(F.data == "back")
async def on_back(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Back to menu for {callback.from_user.id}")
    try:
        await callback.message.edit_text(
            "Привет, это fastype бот, он поможет вам в тренировке слепой печати.",
            reply_markup=build_start_markup()
        )
    except exceptions.TelegramAPIError as e:
        logger.warning(f"Edit back failed: {e}")
    await state.set_state(States.pick_model)
    await callback.answer()

async def main():
    logger.info("Bot starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

