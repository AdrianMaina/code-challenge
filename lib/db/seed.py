# lib/db/seed.py
import sqlite3
import os # Added os module
import sys # Added sys module

# Add project root to sys.path to allow absolute imports if this script is run directly
# This script is in 'lib/db/', so BASE_DIR (project root) is two levels up.
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT_DIR not in sys.path: # Add only if not already present
    sys.path.append(PROJECT_ROOT_DIR)

# Now use absolute imports as PROJECT_ROOT_DIR (project root) is in sys.path
from lib.db.connection import get_db_connection, DATABASE_NAME # Import DATABASE_NAME for path check
from lib.models.author import Author
from lib.models.magazine import Magazine
from lib.models.article import Article

def seed_database():
    """
    Seeds the database with initial data for authors, magazines, and articles.
    This function assumes that the schema has already been created.
    """
    conn = get_db_connection()
    if not conn:
        print("Seeding failed: Could not connect to the database.")
        return

    try:
        cursor = conn.cursor()

        print("Clearing existing data from articles, authors, and magazines tables...")
        cursor.execute("DELETE FROM articles")
        # Order of deletion matters if there were FK constraints without ON DELETE CASCADE (though ours has it)
        cursor.execute("DELETE FROM authors")
        cursor.execute("DELETE FROM magazines")
        # Reset autoincrement counters for SQLite
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='authors'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='magazines'")
        conn.commit()
        print("Existing data cleared.")

        # --- Seed Authors ---
        print("Seeding authors...")
        author_data = [
            ("J.K. Rowling",),
            ("George R.R. Martin",),
            ("Stephen King",),
            ("Jane Austen",),
            ("Ernest Hemingway",)
        ]
        cursor.executemany("INSERT INTO authors (name) VALUES (?)", author_data)
        conn.commit()
        print(f"{len(author_data)} authors seeded.")

        # Fetch author IDs for linking articles
        authors_from_db = cursor.execute("SELECT id, name FROM authors").fetchall()
        authors = {row["name"]: row["id"] for row in authors_from_db}


        # --- Seed Magazines ---
        print("Seeding magazines...")
        magazine_data = [
            ("Tech Today", "Technology"),
            ("Literary Review", "Literature"),
            ("Science Monthly", "Science"),
            ("Gourmet World", "Food"),
            ("Adventure Times", "Travel")
        ]
        cursor.executemany("INSERT INTO magazines (name, category) VALUES (?, ?)", magazine_data)
        conn.commit()
        print(f"{len(magazine_data)} magazines seeded.")

        # Fetch magazine IDs for linking articles
        magazines_from_db = cursor.execute("SELECT id, name, category FROM magazines").fetchall()
        magazines = {row["name"]: row["id"] for row in magazines_from_db}


        # --- Seed Articles ---
        # (title, content, author_id, magazine_id) - order in Article class constructor
        print("Seeding articles...")
        article_data = [
            # J.K. Rowling articles
            ("The Magic of Storytelling", "An in-depth look at narrative structures.", authors["J.K. Rowling"], magazines["Literary Review"]),
            ("World Building 101", "Tips for creating believable fictional worlds.", authors["J.K. Rowling"], magazines["Literary Review"]),
            ("Exploring Scottish Highlands", "A travelogue inspired by magical landscapes.", authors["J.K. Rowling"], magazines["Adventure Times"]),

            # George R.R. Martin articles
            ("Complex Characters in Epic Fantasy", "Essay on character development.", authors["George R.R. Martin"], magazines["Literary Review"]),
            ("The Future of Interactive Narratives", "Exploring tech in storytelling.", authors["George R.R. Martin"], magazines["Tech Today"]),
            ("The Winds of Winter: A Preview", "A fictional preview for a fictional magazine.", authors["George R.R. Martin"], magazines["Literary Review"]),


            # Stephen King articles
            ("The Art of Suspense", "How to keep readers on the edge of their seats.", authors["Stephen King"], magazines["Literary Review"]),
            ("Horror and Human Psychology", "The science behind fear in fiction.", authors["Stephen King"], magazines["Science Monthly"]),
            ("My Favorite Diner Food", "A surprising take on comfort food from the master of horror.", authors["Stephen King"], magazines["Gourmet World"]),


            # Jane Austen articles
            ("Social Commentary in 19th Century Novels", "Analyzing societal norms through literature.", authors["Jane Austen"], magazines["Literary Review"]),
            ("A Lady's Journey Through Bath", "Travel and society in historical England.", authors["Jane Austen"], magazines["Adventure Times"]),

            # Ernest Hemingway articles
            ("The Iceberg Theory in Writing", "Less is more in prose.", authors["Ernest Hemingway"], magazines["Literary Review"]),
            ("Fishing in the Gulf Stream", "A tale of man and nature.", authors["Ernest Hemingway"], magazines["Adventure Times"]),
            ("A Moveable Feast: Parisian Cafes", "Recollections of food and drink in Paris.", authors["Ernest Hemingway"], magazines["Gourmet World"]),
            ("The Natural World of Cuba", "Observations on Cuban flora and fauna.", authors["Ernest Hemingway"], magazines["Science Monthly"])
        ]

        # Note: The Article.create method could be used here too, but direct INSERTs are fine for seeding.
        # For direct inserts, the order of values must match the table schema.
        # (title, content, author_id, magazine_id)
        sql_insert_article = "INSERT INTO articles (title, content, author_id, magazine_id) VALUES (?, ?, ?, ?)"
        cursor.executemany(sql_insert_article, article_data)
        conn.commit()
        print(f"{len(article_data)} articles seeded.")

        print("Database seeding completed successfully!")

    except sqlite3.Error as e:
        print(f"An SQLite error occurred during seeding: {e}")
        if conn:
            conn.rollback() # Rollback changes if an error occurs
    except KeyError as e:
        print(f"Seeding failed: Could not find pre-seeded author or magazine ID for key {e}. Make sure author/magazine names in article_data match those seeded.")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during seeding: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Attempting to seed the database...")
    # Ensure your schema is created first by running setup_db.py.
    # DATABASE_NAME is imported from lib.db.connection
    db_path_check = os.path.join(PROJECT_ROOT_DIR, DATABASE_NAME)

    if not os.path.exists(db_path_check):
        print(f"Database file '{DATABASE_NAME}' not found at '{db_path_check}'.")
        print("Please run 'python scripts/setup_db.py' first to create the database schema.")
    else:
        # Confirm before wiping and reseeding if data might be important
        # confirm = input("This will clear existing data and re-seed. Are you sure? (yes/no): ")
        # if confirm.lower() == 'yes':
        #     seed_database()
        # else:
        #     print("Seeding cancelled by user.")
        seed_database() # For now, seed directly without confirmation prompt
