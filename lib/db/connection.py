# lib/db/connection.py
import sqlite3

DATABASE_NAME = 'articles.db'

def get_db_connection():
    """
    Establishes a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A connection object to the database.
                            Returns None if connection fails.
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        # This enables column access by name: row['column_name']
        # And also allows access by index: row[0]
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == '__main__':
    # Test the connection
    conn = get_db_connection()
    if conn:
        print(f"Successfully connected to {DATABASE_NAME}")
        # Example: Create a cursor and execute a simple query
        # cursor = conn.cursor()
        # cursor.execute("SELECT sqlite_version();")
        # db_version = cursor.fetchone()
        # print(f"SQLite version: {db_version[0]}")
        conn.close()
        print("Connection closed.")
    else:
        print(f"Failed to connect to {DATABASE_NAME}")

