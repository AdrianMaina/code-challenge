# tests/test_author.py
import pytest
import sqlite3
import os

# Add project root to sys.path to allow imports from lib
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from lib.db.connection import get_db_connection, DATABASE_NAME
from lib.models.author import Author, add_author_with_articles
from lib.models.magazine import Magazine # Needed for relationship tests
from lib.models.article import Article # Needed for relationship tests
from scripts.setup_db import setup_database # To setup schema for tests
from lib.db.seed import seed_database # To seed data for tests

# Test database will be created in the tests directory or use an in-memory DB
TEST_DB_NAME = 'test_articles.db'
ORIGINAL_DB_NAME = DATABASE_NAME # Save the original DB name

@pytest.fixture(scope="session", autouse=True)
def setup_test_database_once():
    """
    Fixture to set up the database schema once for the entire test session.
    This will run before any tests in the session.
    """
    # Temporarily change DATABASE_NAME for connection module to use test DB
    import lib.db.connection
    lib.db.connection.DATABASE_NAME = TEST_DB_NAME

    # Ensure the test database directory exists if it's a file-based DB
    # For 'test_articles.db', it will be created in the root if not specified otherwise.
    # If using a file-based test DB, ensure it's cleaned up.
    db_path = os.path.join(BASE_DIR, TEST_DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)

    print(f"Setting up test database: {TEST_DB_NAME} for the session.")
    # Use the setup_database script logic, but point to TEST_DB_NAME
    # This requires setup_database to be flexible or to replicate its logic here.

    # Simplified setup for test DB:
    conn = sqlite3.connect(TEST_DB_NAME)
    conn.row_factory = sqlite3.Row
    schema_path = os.path.join(BASE_DIR, 'lib', 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        sql_script = f.read()
    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("Test database schema created.")

    yield # This is where the testing happens

    # Teardown: Remove the test database file after all tests in the session are done
    print(f"Tearing down test database: {TEST_DB_NAME}")
    if os.path.exists(db_path):
        os.remove(db_path)
    # Restore original DATABASE_NAME
    lib.db.connection.DATABASE_NAME = ORIGINAL_DB_NAME
    print("Test database torn down.")


@pytest.fixture(autouse=True)
def setup_test_database(setup_test_database_once):
    """
    Fixture to ensure a clean database state for each test function.
    It clears data from tables before each test.
    Relies on the session-scoped fixture to have created the schema.
    """
    conn = get_db_connection() # Should now connect to TEST_DB_NAME
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles")
            cursor.execute("DELETE FROM authors")
            cursor.execute("DELETE FROM magazines")
            # Reset autoincrement counters for SQLite
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='authors'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='magazines'")
            conn.commit()
        finally:
            conn.close()
    else:
        raise Exception("Failed to connect to test database for cleanup.")


class TestAuthor:
    """Tests for the Author class."""

    def test_author_creation_and_save(self):
        """Test creating and saving an author."""
        author = Author(name="Test Author One")
        assert author.id is None
        author.save()
        assert author.id is not None

        fetched_author = Author.get_by_id(author.id)
        assert fetched_author is not None
        assert fetched_author.name == "Test Author One"
        assert fetched_author.id == author.id

    def test_author_name_validation(self):
        """Test author name validation."""
        with pytest.raises(ValueError, match="Author name must be a non-empty string."):
            Author(name="")
        with pytest.raises(ValueError, match="Author name must be a non-empty string."):
            Author(name=123)

        author = Author.create("Valid Name")
        assert author is not None
        with pytest.raises(ValueError, match="Author name must be a non-empty string."):
            author.name = ""


    def test_author_create_method(self):
        """Test the Author.create class method."""
        author = Author.create(name="Test Author Two")
        assert author is not None
        assert author.id is not None
        assert author.name == "Test Author Two"

        fetched_author = Author.get_by_id(author.id)
        assert fetched_author.name == "Test Author Two"

    def test_find_author_by_name(self):
        """Test finding an author by name."""
        Author.create(name="Find Me Author")
        fetched = Author.find_by_name("Find Me Author")
        assert fetched is not None
        assert fetched.name == "Find Me Author"
        assert Author.find_by_name("Non Existent Author") is None

    def test_get_all_authors(self):
        """Test retrieving all authors."""
        authors_before = Author.get_all()
        assert len(authors_before) == 0

        Author.create(name="Author A")
        Author.create(name="Author B")

        authors_after = Author.get_all()
        assert len(authors_after) == 2
        names = {author.name for author in authors_after}
        assert "Author A" in names
        assert "Author B" in names

    def test_author_deletion(self):
        """Test deleting an author."""
        author = Author.create(name="ToDelete")
        author_id = author.id
        assert Author.get_by_id(author_id) is not None

        author.delete()
        assert author.id is None # Should be marked as deleted
        assert Author.get_by_id(author_id) is None

    def test_author_name_setter_updates_db(self):
        """Test that setting the name updates the database."""
        author = Author.create(name="Original Name")
        author_id = author.id
        
        author.name = "Updated Name" # This should trigger save in DB
        # Re-fetch from DB to confirm
        fetched_author = Author.get_by_id(author_id)
        assert fetched_author is not None
        assert fetched_author.name == "Updated Name"

    def test_save_existing_author_updates(self):
        """Test saving an existing author updates their record."""
        author = Author.create("Initial Save")
        author_id = author.id

        author.name = "Updated via Save"
        author.save() # Explicitly call save

        fetched_author = Author.get_by_id(author_id)
        assert fetched_author.name == "Updated via Save"

    def test_author_repr(self):
        """Test the __repr__ method of Author."""
        author = Author(name="Repr Author", id=101)
        assert repr(author) == "<Author id=101 name='Repr Author'>"
        
        unsaved_author = Author(name="Unsaved Repr")
        assert repr(unsaved_author) == "<Author id=None name='Unsaved Repr'>"

    # --- Relationship Tests ---

    def test_author_articles_empty(self):
        """Test author.articles() when there are no articles."""
        author = Author.create("Writer Wo Articles")
        assert author.articles() == []

    def test_author_magazines_empty(self):
        """Test author.magazines() when no contributions."""
        author = Author.create("Writer Wo Magazines")
        assert author.magazines() == []

    def test_author_add_article(self):
        """Test adding an article via author.add_article()."""
        author = Author.create("Productive Writer")
        magazine = Magazine.create("Test Mag", "Testing")
        assert author is not None and author.id is not None
        assert magazine is not None and magazine.id is not None

        article_title = "My First Article via Author"
        article = author.add_article(magazine, article_title, "Some content.")

        assert article is not None
        assert article.id is not None
        assert article.title == article_title
        assert article.author_id == author.id
        assert article.magazine_id == magazine.id

        # Verify it's in the author's articles list
        author_articles = author.articles()
        assert len(author_articles) == 1
        assert author_articles[0].id == article.id
        assert author_articles[0].title == article_title

    def test_author_articles_and_magazines_populated(self):
        """Test author.articles() and author.magazines() with data."""
        author1 = Author.create("Author One")
        mag1 = Magazine.create("Tech Weekly", "Tech")
        mag2 = Magazine.create("Science Daily", "Science")

        # Articles for author1
        article1_1 = author1.add_article(mag1, "Intro to Python", "Content...")
        article1_2 = author1.add_article(mag2, "Quantum Physics Explained", "Content...")
        article1_3 = author1.add_article(mag1, "Advanced Python", "Content...") # Another for mag1

        # Check articles
        author1_articles = author1.articles()
        assert len(author1_articles) == 3
        titles = {art.title for art in author1_articles}
        assert "Intro to Python" in titles
        assert "Quantum Physics Explained" in titles
        assert "Advanced Python" in titles

        # Check magazines (should be unique)
        author1_magazines = author1.magazines()
        assert len(author1_magazines) == 2
        mag_names = {mag.name for mag in author1_magazines}
        assert "Tech Weekly" in mag_names
        assert "Science Daily" in mag_names

    def test_author_topic_areas(self):
        """Test author.topic_areas()."""
        author = Author.create("Diverse Author")
        mag_tech = Magazine.create("Tech Monthly", "Technology")
        mag_lit = Magazine.create("Literary Journal", "Literature")
        mag_sci = Magazine.create("Science World", "Science")
        # Another tech magazine to test uniqueness of categories
        mag_gadget = Magazine.create("Gadget Guide", "Technology")


        author.add_article(mag_tech, "AI Today", "")
        author.add_article(mag_lit, "Modern Poetry", "")
        author.add_article(mag_sci, "Space Exploration", "")
        author.add_article(mag_gadget, "New Smartwatch", "")


        topic_areas = author.topic_areas()
        assert topic_areas is not None
        assert len(topic_areas) == 3 # Technology, Literature, Science
        assert "Technology" in topic_areas
        assert "Literature" in topic_areas
        assert "Science" in topic_areas

        author_no_articles = Author.create("No Articles Yet")
        assert author_no_articles.topic_areas() == []


    def test_add_author_with_articles_transaction(self):
        """Test the transaction function add_author_with_articles."""
        mag1 = Magazine.create("Magazine A", "Category A")
        mag2 = Magazine.create("Magazine B", "Category B")
        assert mag1 and mag2 # Ensure magazines are created

        articles_data = [
            {'title': 'Transaction Article 1', 'content': 'Content 1', 'magazine_id': mag1.id},
            {'title': 'Transaction Article 2', 'content': 'Content 2', 'magazine_id': mag2.id},
        ]

        new_author = add_author_with_articles("Transactional Author", articles_data)
        assert new_author is not False # Function returns author instance on success
        assert new_author.id is not None
        assert new_author.name == "Transactional Author"

        # Verify articles were created and linked
        author_articles = new_author.articles()
        assert len(author_articles) == 2
        titles = {art.title for art in author_articles}
        assert "Transaction Article 1" in titles
        assert "Transaction Article 2" in titles

    def test_add_author_with_articles_transaction_rollback(self):
        """Test rollback if an article has an invalid magazine_id."""
        mag_valid = Magazine.create("Valid Mag", "Valid Cat")
        invalid_magazine_id = 9999 # Assumed not to exist

        articles_data_fail = [
            {'title': 'Good Article', 'content': 'Content', 'magazine_id': mag_valid.id},
            {'title': 'Bad Article', 'content': 'Content', 'magazine_id': invalid_magazine_id},
        ]

        author_name_fail = "Rollback Author"
        result = add_author_with_articles(author_name_fail, articles_data_fail)
        assert result is False # Should fail and return False

        # Verify author was not created (or rolled back)
        assert Author.find_by_name(author_name_fail) is None

        # Verify the 'Good Article' was also not created due to rollback
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE title = ?", ("Good Article",))
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 0

    def test_author_with_most_articles(self):
        """Test finding the author with the most articles."""
        # Setup
        author1 = Author.create("Writer One")
        author2 = Author.create("Writer Two")
        author3 = Author.create("Writer Three")
        mag = Magazine.create("General Mag", "General")

        # Author1: 2 articles
        author1.add_article(mag, "Title A1", "")
        author1.add_article(mag, "Title A2", "")
        # Author2: 3 articles
        author2.add_article(mag, "Title B1", "")
        author2.add_article(mag, "Title B2", "")
        author2.add_article(mag, "Title B3", "")
        # Author3: 1 article
        author3.add_article(mag, "Title C1", "")

        most_prolific = Author.author_with_most_articles()
        assert most_prolific is not None
        assert most_prolific.id == author2.id
        assert most_prolific.name == "Writer Two"

        # Test case with no articles
        # Clear articles and authors again for a clean state for this part
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM authors")
        conn.commit()
        conn.close()
        Author.create("Lonely Writer") # Exists but no articles
        assert Author.author_with_most_articles() is None
