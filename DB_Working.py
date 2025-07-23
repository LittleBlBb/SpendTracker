# DB_Working.py
from itertools import product

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
                conn.commit()
                print("Query executed successfully")
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

def save_user_message(message):
    print(f"Processing saving user message to DB: {message.from_user.id}, {message.from_user.username}")
    insert_query = """
            INSERT INTO messages (user_id, message_text)
            VALUES (
                %s, %s
                )
            """
    values = (
        message.from_user.id,
        message.text
    )

    print(f"Query: {insert_query}, Values: {values}")
    execute_query(insert_query, values)

def insert_parsed_data(message, data):
    print(f"Processing parse for user: {message.from_user.id}, {message.from_user.username}")
    insert_query = """ 
            INSERT INTO transactions (user_id, category_id, amount, transaction_date, product)    
            VALUES (
                %s,
                (SELECT category_id FROM categories WHERE category_name = %s),
                %s,
                %s,
                %s
            )
            """
    values = (
        data["user_id"],
        data["category"],
        data["amount"],
        data["date"],
        data["product"]
    )
    print(f"Query: {insert_query}, Values: {values}")
    execute_query(insert_query, values)

def get_all_transactions_by_user(from_user):
    print(f"Trying to get all transactions by user {from_user.id}, {from_user.username}")

    query = (
        "SELECT c.category_name, t.product, t.amount, TO_CHAR(t.created_at, 'YYYY-MM-DD') AS created_at "
        "FROM TRANSACTIONS t "
        "JOIN categories c "
        "ON c.category_id = t.category_id " 
        "ORDER BY t.created_at"
    )

    values = (from_user.id,)

    print(f"Query: {query}\n Values: {values}")
    query_result = execute_query(query, values, fetch=True)
    print(query_result)

    return query_result

def delete_transaction_by_id(message):
    print(f"Processing delete transaction for user {message.from_user.id}, {message.from_user.username}")

    query = (
        "SELECT t.transaction_id, c.category_name, t.product, t.amount, TO_CHAR(t.created_at, 'YYYY-MM-DD') AS created_at "
        "FROM TRANSACTIONS t "
        "JOIN categories c "
        "ON c.category_id = t.category_id "
        "WHERE t.user_id = %s "
        "ORDER BY t.created_at"
    )

    values = (message.from_user.id,)

    print(f"Query: {query}, Values: {values}")

    transactions = execute_query(query, values, fetch=True)
    transaction_number = int(message.text)
    if not transactions or transaction_number > len(transactions):
        return False
    transaction = transactions[transaction_number - 1]
    transaction_id = transaction[0]
    product = transaction[2]
    amount = transaction[3]

    delete_query = (
        "DELETE FROM TRANSACTIONS "
        "WHERE transaction_id = %s AND user_id = %s"
    )

    delete_values = (transaction_id, message.from_user.id)
    print(f"Delete Query: {delete_query}, Values: {delete_values}")

    execute_query(delete_query, delete_values)

    return True

def new_transaction(message, values):
    print(f"Processing new_transaction for user: {message.from_user.id}, {message.from_user.username}")

    insert_query = (
        "INSERT INTO TRANSACTIONS (user_id, category_id, amount, transaction_date, product) "
        "VALUES (%s, %s, %s, %s, %s)"
    )

    print(f"Query: {insert_query}, Values: {values}")
    execute_query(insert_query, values)

def category_user_choice(message):
    print(f"Processing category_user_choice: {message.from_user.id}, {message.from_user.username}")
    # Проверка, существует ли категория
    check_query = "SELECT category_id FROM categories WHERE category_id = %s"
    check_values = (message.text,)
    result = execute_query(check_query, check_values, fetch=True)

    if result == []:
        print(f"Operation skipped: this category not exists {message.text}.")
        return False
    elif result == False:
        print(f"Incorrected input: Type error {message.text}.")
        return False

def get_all_categories(from_user):
    print(f"Trying to get all categories")

    query = (
        "SELECT category_name FROM categories ORDER BY category_id"
    )

    print(f"Query: {query}")
    query_result = execute_query(query, fetch=True)

    result = '\n'.join(f"{i}. {item[0]}" for i, item in enumerate(query_result[0:], start=1))

    return result

def update_transaction_by_id(message, data):
    print(f"Processing update transaction for user {message.from_user.id}, {message.from_user.username}")

    select_query = (
        "SELECT t.transaction_id, c.category_name, t.product, t.amount, TO_CHAR(t.created_at, 'YYYY-MM-DD') AS created_at "
        "FROM TRANSACTIONS t "
        "JOIN categories c "
        "ON c.category_id = t.category_id "
        "WHERE t.user_id = %s "
        "ORDER BY t.created_at"
    )

    select_values = (message.from_user.id,)

    print(f"Query: {select_query}, Values: {select_values}")

    transactions = execute_query(select_query, select_values, fetch=True)
    transaction_number = int(data.get("update_id"))
    if not transactions or transaction_number > len(transactions):
        return False
    transaction = transactions[transaction_number - 1]
    transaction_id = transaction[0]
    product = transaction[2]
    amount = transaction[3]
    update_field = data.get("update_field")

    update_query = (
        f"UPDATE transactions "
        f"SET {update_field} = %s "
        f"WHERE user_id = %s AND transaction_id = %s"
    )

    update_values = (data.get("updated_field"), message.from_user.id, transaction_id)
    print(f"Update Query: {update_query}, Values: {update_values}")

    execute_query(update_query, update_values)

    return True

def get_transactions():
    query = (
        "SELECT t.transaction_id, c.category_name, t.product, t.amount, TO_CHAR(t.created_at, 'YYYY-MM-DD') AS created_at "
        "FROM TRANSACTIONS t "
        "JOIN categories c "
        "ON c.category_id = t.category_id " 
        "ORDER BY t.created_at"
    )

    result = execute_query(query, fetch=True)

    return [
        {
            "transaction_id": row[0],
            "category_name": row[1],
            "product": row[2],
            "amount": float(row[3]),
            "transaction_date": str(row[4])
        }
        for row in result
    ]


def add_transaction(data):
    query = (
        "INSERT INTO transactions (user_id, category_id, product, amount, transaction_date) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING transaction_id"
    )

    values = (
        data["user_id"],
        data["category_id"],
        data["product"],
        data["amount"],
        data["transaction_date"]
    )

    result = execute_query(query, values, fetch=True)

    return {"transaction_id": result[0][0]} if result else {"status": "failed"}

def delete_transaction(transaction_id):
    print(f"Processing delete transaction {transaction_id}")
    query = "DELETE FROM transactions WHERE transaction_id = %s RETURNING transaction_id"
    result = execute_query(query, (transaction_id,), fetch=True)
    if result:
        return {"status": "deleted", "transaction_id": result[0][0]}
    else:
        return {"error": "transaction not found"}

def update_transaction(transaction_id, data):
    fields = []
    values = []

    for key in ("product", "amount", "transaction_date", "category_id"):
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return {"error" : "No fields to update"}

    values.append(transaction_id)
    query = f"UPDATE transactions SET {', '.join(fields)} WHERE transaction_id = %s"
    execute_query(query, values)

    return {"status": "updated", "transaction_id": transaction_id}

#Начало переписки (/start)
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