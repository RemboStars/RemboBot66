import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CARD_DETAILS = os.getenv("CARD_DETAILS")
PRICE_PER_STAR = 1.5

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Машина состояний
class BuyStars(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

# Главное меню
def main_menu():
    kb = [
        [KeyboardButton(text="💫 Купить звёзды")],
        [KeyboardButton(text="ℹ️ Информация")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Старт
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! 👋 Я бот для покупки звёзд.", reply_markup=main_menu())

# Нажали "Купить звёзды"
@dp.message(F.text == "💫 Купить звёзды")
async def buy_stars(message: types.Message, state: FSMContext):
    await message.answer("Введите количество звёзд, которое хотите купить:")
    await state.set_state(BuyStars.waiting_for_amount)

# Получаем количество
@dp.message(BuyStars.waiting_for_amount, F.text.regexp(r"^\d+$"))
async def process_amount(message: types.Message, state: FSMContext):
    amount = int(message.text)
    total = amount * PRICE_PER_STAR
    await state.update_data(amount=amount, total=total)

    await message.answer(
        f"Сумма к оплате: <b>{total:.2f} ₽</b>\n\n"
        f"Реквизиты для перевода:\n<code>{CARD_DETAILS}</code>\n\n"
        "После оплаты прикрепите сюда квитанцию 📎"
    )
    await state.set_state(BuyStars.waiting_for_receipt)

# Получаем квитанцию
@dp.message(BuyStars.waiting_for_receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    total = data["total"]

    # Уведомляем админа
    await bot.send_message(
        ADMIN_ID,
        f"🛒 Новая покупка!\n"
        f"Пользователь: @{message.from_user.username or message.from_user.id}\n"
        f"Количество: {amount} звёзд\n"
        f"Сумма: {total:.2f} ₽"
    )
    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="Квитанция")
    elif message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption="Квитанция")

    await message.answer("✅ Спасибо! Ваша оплата отправлена на проверку. Ожидайте получения звёзд.")
    await state.clear()

# Обработка некорректного ввода
@dp.message(BuyStars.waiting_for_amount)
async def invalid_amount(message: types.Message):
    await message.answer("Введите число — количество звёзд.")

async def main():
    await dp.start_polling(bot)

if name == "main":
    import asyncio
    asyncio.run(main())
