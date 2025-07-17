# main.py
import asyncio
import logging
import os
import re
import webbrowser
import DB_Working
from aiohttp.http_parser import ParseState
from datetime import datetime
from aiogram import Dispatcher, Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from states import TransactionStates, ParseStates, DeleteStates, UpdateStates
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

# Метод сохранения истории чата
async def save_to_file(message):
    await save_message_to_db(message)
    output_file = f'Chats/{message.from_user.username}_chat.txt'
    with open(output_file, "a", encoding='utf-8') as file:
        msg = message.text.strip() + "\n"
        file.write(msg)

async def save_message_to_db(message):
    DB_Working.save_user_message(message)

#Метод парсинга сообщений
def parse_message(message: types.Message):
    text = message.text.strip()
    data = {}

    patterns = {
        "category": r"категория\s*:\s*(.+?)(?:\n|$)",
        "product": r"товар\s*:\s*(.+?)(?:\n|$)",
        "date": r"дата\s*:\s*(\d{2,4}-\d{2}-\d{2,4})(?:\n|$)",
        "amount": r"сумма\s*:\s*(\d+)(?:\n|$)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()

            if key == "date":
                try:
                    if re.match(r"\d{4}-\d{2}-\d{2}$", value):  # yyyy-mm-dd
                        parsed_date = datetime.strptime(value, "%Y-%m-%d")
                    elif re.match(r"\d{2}-\d{2}-\d{4}$", value):  # dd-mm-yyyy
                        parsed_date = datetime.strptime(value, "%d-%m-%Y")
                    else:
                        raise ValueError("Неверный формат даты (только с тире)")
                    value = parsed_date.strftime("%Y-%m-%d")
                except Exception as e:
                    print(f"Ошибка обработки даты: {e}")
                    return None

            data[key] = value

    data["user_id"] = str(message.from_user.id)

    if not any(key in data for key in patterns):
        print("Не удалось распарсить сообщение.")
        return None

    return data

#функция сохранения в бд для парсинга
def save_parsed_data_to_database(message, data):
    try:
        DB_Working.insert_parsed_data(message, data)
        print("Данные успешно сохранены")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в БД {e}")
        return False

#функция парсящая и созраняющая в БД
async def parse_and_save_message(message: types.Message):
    await save_to_file(message)
    parsed_data = parse_message(message)
    if not parsed_data:
        return False
    return save_parsed_data_to_database(message, parsed_data)

#проверка на валидность введенной стоимости
def is_valid_amount(text):
    pattern = r'^\d+(\.\d{1,2})?$'
    return bool(re.match(pattern, text)) and float(text) > 0

# Обработка различных команд
@dp.message(CommandStart())
async def cmd_start(message: Message):
    DB_Working.start(message)
    await message.answer(f'Привет, {message.from_user.first_name}')
    await save_to_file(message)

#функция для парсинга сообщения без последовательного ввода данных
@dp.message(Command("parse"))
async def parse(message: Message, state: FSMContext):
    await save_to_file(message)
    await message.answer(
        "Введите сообщение по следующему примеру:\n\n"
        "Категория: Транспорт\n"
        "Товар: Бензин\n"
        "Дата: 2025-07-07\n"
        "Сумма: 1500"
    )
    await state.set_state(ParseStates.waiting_for_input)

@dp.message(ParseStates.waiting_for_input)
async def user_input_parsing_str(message: Message, state: FSMContext):
    success = parse_and_save_message(message)
    if success:
        await message.answer("Данные успешно сохранены.")
    else:
        await message.answer("Неверный формат. Проверьте сообщение.")
    await state.clear()

#============добавить транзакцию=============
@dp.message(Command("new_transaction"))
async def new_transaction(message: Message, state: FSMContext):
    await save_to_file(message)
    all_categories = DB_Working.get_all_categories(message.from_user)
    await message.answer(f"Выберите номер категории, которой принадлежит ваш платеж:\n\n{all_categories}")

    await state.set_state(TransactionStates.choosing_category)

@dp.message(TransactionStates.choosing_category)
async def category_choice(message: Message, state: FSMContext):
    await save_to_file(message)
    if (DB_Working.category_user_choice(message) == False):
        await message.answer("Выбранной категории не существует, попробуйте снова.")
        return

    await state.update_data(category_id=message.text.strip())
    await message.answer("Введите название товара:")
    await state.set_state(TransactionStates.entering_product)

@dp.message(TransactionStates.entering_product)
async def product_input(message: Message, state: FSMContext):
    await save_to_file(message)
    product = message.text.capitalize()

    await state.update_data(product=product)
    await message.answer("Введите дату покупки:")
    await state.set_state(TransactionStates.entering_date)

@dp.message(TransactionStates.entering_date)
async def date_input(message: Message, state: FSMContext):
    await save_to_file(message)
    raw_date = message.text.strip()

    patterns = [
        ("%Y-%m-%d", r"^\d{4}-\d{2}-\d{2}$"),
        ("%d-%m-%Y", r"^\d{2}-\d{2}-\d{4}$"),
    ]

    parsed_date = None

    for fmt, regex in patterns:
        if re.match(regex, raw_date):
            try:
                parsed_date = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                pass

    if parsed_date is None:
        await message.answer(
            "Неверный формат даты. Пожалуйста, введите дату в одном из следующих форматов:\n"
            "'yyyy-mm-dd', 'dd-mm-yyyy', 'yyyy/mm/dd', 'dd-mm-yyyy'",
            parse_mode="Markdown"
        )
        return


    await state.update_data(date=str(parsed_date))
    await message.answer("Введите сумму покупки: ")
    await state.set_state(TransactionStates.entering_amount)

@dp.message(TransactionStates.entering_amount)
async def amount_input(message: Message, state: FSMContext):
    await save_to_file(message)

    if(is_valid_amount(message.text) == False):
        await message.answer("Неверный формат. Введите целое или вещественное положительное число.")
        return
    data = await state.get_data()

    values = (
        message.from_user.id,
        data.get("category_id"),
        message.text.strip(),
        data.get("date"),
        data.get("product")
    )
    DB_Working.new_transaction(message, values)

    await state.clear()

#============вывести все транзакции=============
@dp.message(Command("show_all_transactions"))
async def show_all_transactions(message: Message):
    await save_to_file(message)
    all_transactions = DB_Working.get_all_transactions_by_user(message.from_user)

    if not all_transactions:
        await message.answer("У вас пока нет покупок.")
        return

    col_widths = {
        "number": 4,
        "category": 12,
        "product": 12,
        "amount": 10,
        "date": 10
    }

    header = (
        f"{'№':<{col_widths['number']}} "
        f"{'Категория':<{col_widths['category']}} "
        f"{'Товар':<{col_widths['product']}} "
        f"{'Сумма':<{col_widths['amount']}} "
        f"{'Дата':<{col_widths['date']}}"
    )

    formatted_transactions = [
        f"{i+1:<{col_widths['number']}} "
        f"{t[0]:<{col_widths['category']}} "
        f"{t[1]:<{col_widths['product']}} "
        f"{float(t[2]):<{col_widths['amount']}} "
        f"{t[3]:<{col_widths['date']}}"

        for i, t in enumerate(all_transactions)
    ]

    response = ("Все введенные вами покупки:\n\n" + header +
                "\n" + "-" * 48 + "\n" +
                "\n".join(formatted_transactions))

    await message.answer(f"```{response}```", parse_mode="Markdown")

#============удалить транзакцию=================
@dp.message(Command("delete_transaction"))
async def delete_transaction(message: Message, state: FSMContext):
    await save_to_file(message)
    await show_all_transactions(message)
    await message.answer("Введите номер транзакции, которую хотите удалить:")
    await state.set_state(DeleteStates.delete_id)

@dp.message(DeleteStates.delete_id)
async def input_transaction_id(message: Message, state: FSMContext):
    if(not message.text.isdigit()):
        await message.reply("Нужно указать номер транзакции, например: 3")
        return

    transaction_number = int(message.text)
    if transaction_number < 1:
        await message.reply("Номер транзакции должен быть больше 0")
        return

    if DB_Working.delete_transaction_by_id(message):
        await message.reply("Готово!")
        await show_all_transactions(message)

    await state.clear()

#============обновить транзакцию================
@dp.message(Command("update_transaction"))
async def update_transaction(message: Message, state: FSMContext):
    await save_to_file(message)
    await show_all_transactions(message)
    await message.answer("Введите номер транзакции, которую хотите поменять:")
    await state.set_state(UpdateStates.update_id)

@dp.message(UpdateStates.update_id)
async def input_update_id(message: Message, state: FSMContext):
    await save_to_file(message)
    if (not message.text.isdigit()):
        await message.reply("Нужно указать номер транзакции, например: 3")
        return

    transaction_number = int(message.text)
    if transaction_number < 1:
        await message.answer("Номер транзакции должен быть больше 0")
        return

    await state.update_data(update_id=message.text.strip())
    await message.answer("Введите поле, которое вы хотите поменять:")
    await state.set_state(UpdateStates.update_field)

@dp.message(UpdateStates.update_field)
async def input_update_field(message: Message, state: FSMContext):
    await save_to_file(message)

    await state.update_data(update_field=message.text.strip())
    await message.answer("Введите измененное значение:")
    await state.set_state(UpdateStates.updated_field)

@dp.message(UpdateStates.updated_field)
async def input_updated_field(message: Message, state: FSMContext):
    await save_to_file(message)
    await state.update_data(updated_field=message.text.strip())
    data = await state.get_data()

    if DB_Working.update_transaction_by_id(message, data) == True:
        await message.reply("Готово!")
        await show_all_transactions(message)

    await state.clear()

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer('<b>help</b> <a href="https://github.com/LittleBlBb"><em><u>information</u></em></a>',
                         parse_mode="HTML")
    await save_to_file(message)

@dp.message(Command(commands=['site', 'website']))
async def site_command(message: Message):
    webbrowser.open('https://github.com/LittleBlBb')
    await save_to_file(message)

# Обработка сообщения пользователя
@dp.message(F.text)
async def handle_other_messages(message: Message):
    if message.text.lower() == 'привет':
        await cmd_start(message)
    elif message.text.lower() == 'id':
        await message.answer(f'ID: {message.from_user.id}')
        await save_to_file(message)
    else:
        print(message.chat.id)
        await save_to_file(message)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))