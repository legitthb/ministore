# database.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='ministore_user',
        password='admin',
        database='ministore'
    )
