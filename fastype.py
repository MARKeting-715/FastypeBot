from __future__ import annotations

import asyncio
import html
import os
from contextlib import suppress
from itertools import zip_longest
from time import monotonic

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ai_models.deepseek import deepseek
from ai_models.gemini import gemini
from ai_models.llama import llama
from ai_models.mistral import mistral
from ai_models.qwen import qwen
from ai_models.shared import DEFAULT_ERROR_MESSAGE


DEFAULT_MODEL = "gemini"
MODEL_HANDLERS = {
    "gemini": gemini,
    "llama": llama,
    "deepseek": deepseek,
    "mistral": mistral,
    "qwen": qwen,
}
MODEL_TITLES = {
    "gemini": "Gemini",
    "llama": "Llama",
    "deepseek": "DeepSeek",
    "mistral": "Mistral",
    "qwen": "Qwen",
}


def load_bot_token() -> str:
    for env_name in ("BOT_TOKEN", "API_KEY"):
        token = os.getenv(env_name)
        if token:
            return token

    try:
        from config import API_KEY as config_api_key  # type: ignore
    except Exception:
        config_api_key = None

    if config_api_key:
        return config_api_key

    raise RuntimeError(
        "Telegram bot token is not configured. Set BOT_TOKEN, API_KEY, or config.py"
    )


bot = Bot(token=load_bot_token())
dp = Dispatcher()


class Typing(StatesGroup):
    waiting_for_sentence = State()


def build_main_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать", callback_data="start_game")],
            [InlineKeyboardButton(text="Выбрать модель", callback_data="change_model")],
        ]
    )


def build_end_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Продолжить", callback_data="start_game"),
                InlineKeyboardButton(text="Назад", callback_data="back"),
            ]
        ]
    )


def build_back_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back")]]
    )


def build_models_markup(current_model: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for model_name, model_title in MODEL_TITLES.items():
        label = f"{model_title} ✓" if model_name == current_model else model_title
        builder.add(
            InlineKeyboardButton(text=label, callback_data=f"model:{model_name}")
        )

    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()


def highlight_sentence(reference: str, attempt: str) -> tuple[str, int]:
    reference_chars = list(reference)
    attempt_chars = list(attempt)
    highlighted: list[str] = []
    errors = 0

    for ref_char, user_char in zip_longest(reference_chars, attempt_chars, fillvalue=""):
        is_same = ref_char == user_char or (
            ref_char
            and user_char
            and ref_char.lower() in {"е", "ё"}
            and user_char.lower() in {"е", "ё"}
        )

        if is_same:
            highlighted.append(html.escape(ref_char))
            continue

        wrong_char = ref_char if ref_char else user_char
        highlighted.append(f"<b><u>{html.escape(wrong_char)}</u></b>")
        errors += 1

    return "".join(highlighted), errors


def compute_stats(reference: str, elapsed_seconds: float, errors: int) -> tuple[float, float]:
    effective_time = max(elapsed_seconds, 0.001)
    word_count = max(len(reference.split()), 1)
    visible_chars = max(len([char for char in reference if not char.isspace()]), 1)

    speed = round(word_count / (effective_time / 60), 1)
    accuracy = max(0.0, round((1 - errors / visible_chars) * 100, 1))
    return speed, accuracy


async def safe_delete_message(chat_id: int, message_id: int) -> None:
    with suppress(Exception):
        await bot.delete_message(chat_id=chat_id, message_id=message_id)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    current_model = (await state.get_data()).get("ai", DEFAULT_MODEL)
    await state.clear()
    await state.update_data(ai=current_model)
    await safe_delete_message(message.chat.id, message.message_id)

    model_title = MODEL_TITLES.get(current_model, MODEL_TITLES[DEFAULT_MODEL])

    await message.answer(
        "Привет, это Fastype Bot. Я помогу потренировать слепую печать.\n\n"
        f"Текущая модель: {model_title}",
        reply_markup=build_main_markup(),
    )


@dp.callback_query(F.data == "change_model")
async def change_model(callback: CallbackQuery, state: FSMContext) -> None:
    current_model = (await state.get_data()).get("ai", DEFAULT_MODEL)
    await callback.message.edit_text(
        "Выберите модель",
        reply_markup=build_models_markup(current_model),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("model:"))
async def select_model(callback: CallbackQuery, state: FSMContext) -> None:
    model_name = callback.data.split(":", 1)[1]
    if model_name not in MODEL_HANDLERS:
        await callback.answer("Неизвестная модель", show_alert=True)
        return

    await state.update_data(ai=model_name)
    await callback.message.edit_text(
        "Выберите модель",
        reply_markup=build_models_markup(model_name),
    )
    await callback.answer(f"Выбрана {MODEL_TITLES[model_name]}")


@dp.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery, state: FSMContext) -> None:
    current_model = (await state.get_data()).get("ai", DEFAULT_MODEL)
    model_handler = MODEL_HANDLERS.get(current_model, gemini)

    await callback.answer("Это может занять несколько секунд")
    sentence = await model_handler()

    if sentence == DEFAULT_ERROR_MESSAGE:
        await state.clear()
        await state.update_data(ai=current_model)
        await callback.message.edit_text(
            "Не удалось получить текст от выбранной модели. "
            "Попробуйте другую модель или повторите позже.",
            reply_markup=build_main_markup(),
        )
        return

    await state.update_data(
        ai=current_model,
        text=sentence,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        started_at=monotonic(),
    )
    await state.set_state(Typing.waiting_for_sentence)

    await callback.message.edit_text(
        sentence,
        reply_markup=build_back_markup(),
    )


@dp.message(Typing.waiting_for_sentence, F.text)
async def checking(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    reference = data.get("text")
    if not reference:
        await state.clear()
        return

    attempt = message.text or ""
    await safe_delete_message(message.chat.id, message.message_id)

    elapsed_seconds = monotonic() - data.get("started_at", monotonic())
    highlighted, errors = highlight_sentence(reference, attempt)
    speed, accuracy = compute_stats(reference, elapsed_seconds, errors)

    extra_note = ""
    if reference == DEFAULT_ERROR_MESSAGE:
        extra_note = (
            "\n\n<i>При вводе этого текста вы, возможно, нашли пасхалку.</i>"
        )

    result_text = (
        f"{highlighted}\n\n"
        f"{html.escape(attempt)}\n\n"
        f"Вы справились за {elapsed_seconds:.2f} секунды.\n"
        f"Ваша скорость печати была {speed} слов в минуту.\n"
        f"Ваша точность {accuracy}%."
        f"{extra_note}"
    )

    await bot.edit_message_text(
        text=result_text,
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        reply_markup=build_end_markup(),
        parse_mode="HTML",
    )
    current_model = data.get("ai", DEFAULT_MODEL)
    await state.clear()
    await state.update_data(ai=current_model)


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext) -> None:
    current_model = (await state.get_data()).get("ai", DEFAULT_MODEL)
    await state.clear()
    await state.update_data(ai=current_model)
    await callback.message.edit_text(
        "Привет, это Fastype Bot. Я помогу потренировать слепую печать.",
        reply_markup=build_main_markup(),
    )
    await callback.answer()


@dp.message()
async def ignore_messages(message: Message) -> None:
    await safe_delete_message(message.chat.id, message.message_id)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
