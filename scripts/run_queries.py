# scripts/run_queries.py
import os
import sys
import sqlite3 # Added sqlite3 import

# Add the parent directory (code-challenge) to the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from lib.db.connection import get_db_connection
from lib.models.author import Author
from lib.models.magazine import Magazine
from lib.models.article import Article
from lib.db.seed import seed_database # To ensure there's data
from scripts.setup_db import setup_database # To ensure schema exists

def display_results(title, results):
    """Helper function to display query results neatly."""
    print(f"\n--- {title} ---")
    if results is None: # Handle None results explicitly
        print("No results found or query returned None.")
        print("--- End ---")
        return
    if not results: # Handle empty lists or other falsey but not None results
        print("No results found (empty list/sequence).")
        print("--- End ---")
        return

    # Check if results is a list and if it's not empty before accessing results[0]
    if isinstance(results, list) and len(results) > 0:
        if isinstance(results[0], (Author, Magazine, Article)):
            for item in results:
                print(item) # Relies on the __repr__ method of the models
        elif isinstance(results[0], sqlite3.Row): # For direct SQL results like counts
             for row in results:
                print(dict(row)) # Convert Row to dict for readable printing
        elif isinstance(results[0], str): # For lists of strings like topic_areas or article_titles
            for item in results:
                print(f"- {item}")
        else: # Fallback for other list types
            for item in results:
                print(item)
    elif isinstance(results, (Author, Magazine, Article)): # Single model instance
        print(results)
    elif isinstance(results, sqlite3.Row): # Single Row instance
        print(dict(results))
    elif isinstance(results, dict): # For single dict results (already handled by Row conversion)
        for key, value in results.items():
            print(f"{key}: {value}")
    else: # Fallback for other single item types
        print(results)
    print("--- End ---")

def run_all_queries():
    """
    Runs a series of example queries using the model methods
    and displays the results.
    """
    print("Running example queries...")

    # --- Author Queries ---
    print("\nFetching first author (if any)...")
    all_authors = Author.get_all()
    first_author = all_authors[0] if all_authors else None

    if first_author:
        display_results(f"Articles by Author: {first_author.name} (ID: {first_author.id})", first_author.articles())
        display_results(f"Magazines Author {first_author.name} contributed to", first_author.magazines())
        display_results(f"Topic Areas for Author: {first_author.name}", first_author.topic_areas())
    else:
        print("No authors found to run detailed author queries.")

    display_results("Author with the most articles", Author.author_with_most_articles())

    # --- Magazine Queries ---
    print("\nFetching first magazine (if any)...")
    all_magazines = Magazine.get_all()
    first_magazine = all_magazines[0] if all_magazines else None

    if first_magazine:
        display_results(f"Articles in Magazine: {first_magazine.name}", first_magazine.articles())
        display_results(f"Contributors to Magazine: {first_magazine.name}", first_magazine.contributors())
        display_results(f"Article titles in Magazine: {first_magazine.name}", first_magazine.article_titles())
        display_results(f"Authors with > 2 articles in {first_magazine.name}", first_magazine.contributing_authors())
    else:
        print("No magazines found to run detailed magazine queries.")

    display_results("Magazines with articles by at least 2 different authors", Magazine.magazines_with_articles_by_min_authors(min_authors=2))
    display_results("Number of articles in each magazine", Magazine.article_counts_per_magazine())
    display_results("Magazine with the most articles (Top Publisher)", Magazine.top_publisher())


    # --- Article Queries ---
    print("\nFetching first article (if any)...")
    all_articles = Article.get_all()
    first_article = all_articles[0] if all_articles else None
    if first_article:
        display_results(f"Details for Article ID: {first_article.id}", first_article)
        display_results(f"Author of Article ID: {first_article.id}", first_article.author)
        display_results(f"Magazine for Article ID: {first_article.id}", first_article.magazine)
    else:
        print("No articles found to run detailed article queries.")

    # --- General Queries from Challenge Description ---
    # 1. Get all articles written by a specific author (demonstrated above with first_author.articles())
    # 2. Find all magazines a specific author has contributed to (demonstrated above with first_author.magazines())

    # 3. Get all authors who have written for a specific magazine
    if first_magazine:
        # This is equivalent to first_magazine.contributors()
        display_results(f"Authors who wrote for '{first_magazine.name}' (using magazine.contributors())", first_magazine.contributors())
    else:
        print("Skipping query 3: No first magazine found.")

    # 4. Find magazines with articles by at least 2 different authors (demonstrated above with Magazine.magazines_with_articles_by_min_authors(2))
    # 5. Count the number of articles in each magazine (demonstrated above with Magazine.article_counts_per_magazine())
    # 6. Find the author who has written the most articles (demonstrated above with Author.author_with_most_articles())


    print("\nAll example queries complete.")

if __name__ == '__main__':
    db_file = os.path.join(BASE_DIR, 'articles.db') # Assuming DATABASE_NAME is 'articles.db'
    if not os.path.exists(db_file):
        print(f"Database file '{db_file}' not found.")
        print("Please run 'python scripts/setup_db.py' to create the database schema,")
        print("and then 'python lib/db/seed.py' to populate it with data before running queries.")
    else:
        run_all_queries()
