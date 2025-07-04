# DB_Working.py
from DB_Connection import DB_Connection
import psycopg2


def execute_query(query, values=None, fetch=False):
    db = DB_Connection()
    if db:
        conn = db.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, values)
            if fetch:
                result = cur.fetchall()
                return result
            conn.commit()
            print("Query executed successfully")
            return True
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                print(f"Operation failed: User with ID {values[0]} already exists in the table.")
            return False
        finally:
            cur.close()
            # Не закрываем соединение здесь, оставляем для деструктора


def start(message):
    print(f"Processing user: {message.from_user.id}, {message.from_user.username}")
    # Проверка, существует ли пользователь
    check_query = "SELECT user_id FROM USERS WHERE user_id = %s"
    check_values = (message.from_user.id,)
    result = execute_query(check_query, check_values, fetch=True)

    if result:
        print(f"Operation skipped: User with ID {message.from_user.id} already exists in the table.")
        return

    # Если пользователь не существует, выполняем вставку
    insert_query = (
        "INSERT INTO USERS (user_id, username, first_name, last_name) "
        "VALUES (%s, %s, %s, %s)"
    )
    insert_values = (
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or ""
    )
    print(f"Query: {insert_query}, Values: {insert_values}")
    execute_query(insert_query, insert_values)