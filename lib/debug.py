# lib/debug.py
import os
import sys

# Add the parent directory (code-challenge) to the Python path
# to allow imports from lib.models, lib.db, etc.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from lib.db.connection import get_db_connection
from lib.models.author import Author, add_author_with_articles
from lib.models.magazine import Magazine
from lib.models.article import Article
from lib.db.seed import seed_database # Optional: for easy reseeding
from scripts.setup_db import setup_database # Optional: for easy db setup

def main():
    """
    Main function to start the interactive debugging session.
    """
    print("Starting interactive debugging session...")
    print("Available models: Author, Magazine, Article")
    print("Available functions: add_author_with_articles, seed_database, setup_database")
    print("Database connection: get_db_connection()")
    print("Type 'exit()' or 'quit()' or Ctrl-D to exit.")

    # Example: Create some data if tables are empty or for quick testing
    # This is just an example, you might want to run seed_database() separately
    # or check if data exists before inserting.

    # conn = get_db_connection()
    # if conn:
    #     try:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT COUNT(*) FROM authors")
    #         author_count = cursor.fetchone()[0]
    #         if author_count == 0:
    #             print("Database appears empty. Consider running seed_database() or setup_db.py then seed_database().")
    #             # Example: Create a quick author and magazine for testing
    #             # author1 = Author.create("Debug Author")
    #             # magazine1 = Magazine.create("Debug Weekly", "Debugging")
    #             # if author1 and magazine1:
    #             #     article1 = author1.add_article(magazine1, "My First Debug Article", "Content here.")
    #             #     print(f"Created: {author1}, {magazine1}, {article1}")
    #     except Exception as e:
    #         print(f"Error checking database state: {e}")
    #         print("Ensure your database is set up (python scripts/setup_db.py) and seeded (python lib/db/seed.py).")
    #     finally:
    #         conn.close()


    # Start an interactive Python session
    # This will make local variables (Author, Magazine, etc.) available.
    # For a more robust REPL, consider using IPython if available.
    try:
        from IPython import embed
        print("IPython detected. Starting IPython session.")
        embed()
    except ImportError:
        print("IPython not found. Starting standard Python REPL.")
        import code
        variables = globals().copy()
        variables.update(locals())
        shell = code.InteractiveConsole(variables)
        shell.interact()

if __name__ == '__main__':
    # Ensure DB is set up before debug session
    # You can uncomment these lines if you want to ensure DB setup/seed on debug start.
    # However, it's often better to do this manually so you control when data is reset.
    # print("Ensuring database is set up...")
    # setup_database()
    # print("Ensuring database is seeded...")
    # seed_database()
    # print("-" * 30)

    main()
