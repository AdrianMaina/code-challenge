# scripts/setup_db.py
import sqlite3
import os
import sys # Added sys module

# Add project root to sys.path to allow imports from lib
# This script is in 'scripts/', so BASE_DIR (project root) is one level up from its parent.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path: # Add only if not already present
    sys.path.append(BASE_DIR)

# Now that BASE_DIR is in sys.path, this import should work
from lib.db.connection import get_db_connection, DATABASE_NAME # Import DATABASE_NAME as well

# SCHEMA_PATH and DB_PATH are now correctly defined relative to BASE_DIR
SCHEMA_PATH = os.path.join(BASE_DIR, 'lib', 'db', 'schema.sql')
# DATABASE_NAME from connection.py is just the filename, DB_PATH is its full path
DB_PATH = os.path.join(BASE_DIR, DATABASE_NAME)

def setup_database():
    """
    Sets up the database by executing the schema.sql file.
    It will create the tables defined in schema.sql.
    If the database file already exists, it might be overwritten or appended to,
    depending on the SQL in schema.sql (DROP TABLE IF EXISTS handles this).
    """
    print(f"Database will be created/updated at: {DB_PATH}")
    print(f"Reading schema from: {SCHEMA_PATH}")

    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: Schema file not found at {SCHEMA_PATH}")
        return

    conn = None # Initialize conn to None
    try:
        # Connect to the database. If it doesn't exist, it will be created.
        # get_db_connection() will use DATABASE_NAME which is now correctly located by DB_PATH logic
        conn = get_db_connection()
        if not conn:
            print("Failed to establish database connection. Setup aborted.")
            return

        cursor = conn.cursor()

        with open(SCHEMA_PATH, 'r') as f:
            sql_script = f.read()

        # Execute the SQL script from schema.sql
        # `executescript` can run multiple SQL statements
        cursor.executescript(sql_script)
        conn.commit()
        print("Database schema created/updated successfully.")
        print(f"Tables created: authors, magazines, articles (and indexes).")

    except sqlite3.Error as e:
        print(f"An error occurred during database setup: {e}")
        if conn:
            conn.rollback()
    except FileNotFoundError:
        print(f"Error: Could not read schema file at {SCHEMA_PATH}")
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Setting up the database...")
    setup_database()
    # Optionally, after setting up the schema, you could call the seeder.
    # This is often done as a separate step by the user.
    # print("\nTo seed the database with initial data, run: python lib/db/seed.py")
