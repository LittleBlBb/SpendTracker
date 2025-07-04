# main.py
import os

import telebot
import webbrowser
import DB_Working
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Метод сохранения истории чата
def save_to_file(message):
    output_file = f'Chats/{message.from_user.username}_chat.txt'
    with open(output_file, "a", encoding='utf-8') as file:
        msg = message.text + "\n"
        msg.strip()
        file.write(msg)

# Обработка различных команд
@bot.message_handler(commands=['start'])
def start(message):
    DB_Working.start(message)
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}')
    save_to_file(message)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '<b>help</b> <a href="https://github.com/LittleBlBb"><em><u>information</u></em></a>', parse_mode="html")
    save_to_file(message)

@bot.message_handler(commands=['site', 'website'])
def site(message):
    webbrowser.open('https://github.com/LittleBlBb')
    save_to_file(message)

# Обработка сообщения пользователя
@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        start(message)
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')
        print(message.from_user)
        save_to_file(message)
    else:
        save_to_file(message)

if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Bot polling error: {e}")