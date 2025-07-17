Требуемая версия Python: 3.13.2
## Стандартные библиотеки Python
- asyncio
- datetime
- logging
- os
- re
- webbrowser

## Внешние библиотеки:
- aiohttp==3.12.13
- aiogram==3.21.0
- python-dotenv==1.1.1
- psycopg2==2.9.10

## Установка
1. Установите Python 3.13.2.
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   venv\Scripts\activate
3. Установите зависимости:
    ```bash
   pip install -r requirements.txt
4. Создайте файл .env с переменной TELEGRAM_BOT_TOKEN.
5. Запустите бота:
    ```bash
   python main.py