import asyncio
from itertools import zip_longest
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from time import time

from pydantic.v1.utils import almost_equal_floats

from config import API_KEY
from ai_models.llama import llama
from ai_models.gemini import gemini
from ai_models.deepseek import deepseek
from ai_models.mistral import mistral
from ai_models.qwen import qwen

models = {
    "gemini": gemini,
    "llama": llama,
    "deepseek": deepseek,
    "mistral": mistral,
    "qwen": qwen

}

bot = Bot(API_KEY)

dp = Dispatcher()

class AI(StatesGroup):
    ai = State()

class Text(StatesGroup):
    text = State()
    user_text = State()
    chat_id = State()
    message_id = State()
    time = State()

class Anything(StatesGroup):
    anything = State()

async def sentence_checking(text, user_text):
    ref_words = text.split()
    user_words = user_text.split()
    output_text = ""
    errors = 0
    for ref_word, user_word in zip_longest(ref_words, user_words, fillvalue=""):
        for ref_letter, user_letter in zip_longest(ref_word, user_word, fillvalue=""):
            if (ref_letter == user_letter or
                (ref_letter in "её" and user_letter in "её")):
                output_text += ref_letter
            else:
                output_text += f"<b><u>{ref_letter}</u></b>"
                errors += 1
        output_text += " "
    return output_text.strip(), errors

start_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Начать", callback_data="start_game")],
    # [InlineKeyboardButton(text="Выбрать язык", callback_data="change_language")],
    [InlineKeyboardButton(text="Выбрать модель", callback_data="change_model")]
])

endgame_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Продолжить", callback_data="start_game"), InlineKeyboardButton(text="Назад", callback_data="back")]
])

back_markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Назад", callback_data="back")]
])

@dp.message(CommandStart())
async def start(message: Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    setup_markup = InlineKeyboardBuilder()
    for ai in ["gemini", "llama", "deepseek", "qwen"]:
        setup_markup.add(InlineKeyboardButton(text=ai, callback_data=ai))
    await message.answer("Привет, это fastype бот, он поможет вам в тренировке слепой печати.", reply_markup=start_markup)

@dp.callback_query(F.data.in_(["change_model", "gemini", "llama", "deepseek", "mistral", "qwen"]))
async def change_model(callback: CallbackQuery, state: FSMContext):
    if callback.data in ["gemini", "llama", "deepseek", "mistral", "qwen"]:
        await state.update_data(ai=callback.data)
    current_ai = (await state.get_data()).get("ai", "gemini")
    models_markup = InlineKeyboardBuilder()
    for ai in ["gemini", "llama", "deepseek", "mistral", "qwen"]:
        ai_name = f"{ai} ✅" if ai == current_ai else ai
        models_markup.add(InlineKeyboardButton(text=ai_name, callback_data=ai))
    models_markup.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    await bot.edit_message_text(
        text="Выберите модель",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=models_markup.adjust(1).as_markup()
    )

@dp.callback_query(F.data == "start_game")
async def start_game(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Это может занять некоторое время")
    func = models.get((await state.get_data()).get("ai", "gemini"), gemini)
    await state.update_data(text=await func())
    answer = (await state.get_data()).get("text")
    await state.update_data(chat_id = callback.message.chat.id, message_id = callback.message.message_id)
    await bot.edit_message_text(
        text=answer,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=back_markup
    )
    await state.set_state(Text.user_text)
    await state.update_data(time = time())

@dp.message(Text.user_text)
async def checking(message: Message, state: FSMContext):
    await state.update_data(user_text = message.text)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    data = await state.get_data()
    time_result = time() - data["time"]
    text_result, errors = await sentence_checking(data["text"], data["user_text"])
    await bot.edit_message_text(
        text=f"{text_result}\n\n{data["user_text"]}\n\nВы справились за {round(time_result, 2)} секунд\nВаша скорость печати была {round(len(text_result.split())/(time_result/60), 1)} слов в минуту\nВаша аккуратность {100 - round((errors / len("".join(ch for ch in text_result if ch != " "))) * 100, 1)}%{"\n\n*При вводе этого нелепого текста вы наполняетесь решимостью*\n(пасхалка найдена!)" if data["text"] == "Не удалось получит ответ, смените модель на другую доступную" else ""}",
        chat_id=data["chat_id"],                                                                                                   #Делим кол-во слов на время в минутах                                               #Кол-во ошибок делим на кол-во символов без пробелов(берем через сокр. цикл for все, кроме пробела, и соединяем с помощью join)     попробуйте найти пасхалку)
        message_id=data["message_id"],
        reply_markup=endgame_markup,
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery, state: FSMContext):
    await bot.edit_message_text(
        text="Привет, это fastype бот, он поможет вам в тренировке слепой печати.",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=start_markup
    )
    await state.set_state(Anything.anything)

@dp.message(Anything.anything)
@dp.message()
async def anything(message: Message):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
