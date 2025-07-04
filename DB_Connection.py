# DB_Connection.py
import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

class DB_Connection:
    instance = None
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(DB_Connection, cls).__new__(cls)
            try:
                cls.instance.connection = psycopg2.connect(
                    dbname=os.getenv('DB_NAME'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    host=os.getenv('DB_HOST'),
                    port=os.getenv('DB_PORT')
                )
                print("CONNECTED!")
            except psycopg2.Error as error:
                print("Error with connection to DB", error)
                cls.instance = None
        return cls.instance

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection is not None and not self.connection.closed:
            self.connection.close()
            print("CLOSED!")
            DB_Connection.instance = None

    def __del__(self):
        self.close_connection()