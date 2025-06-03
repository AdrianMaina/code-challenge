# tests/test_article.py
import pytest
import sqlite3
import os

# Add project root to sys.path
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from lib.db.connection import get_db_connection, DATABASE_NAME
from lib.models.article import Article
from lib.models.author import Author
from lib.models.magazine import Magazine

# Use the same test DB setup
TEST_DB_NAME = 'test_articles.db' # Should match other test files
ORIGINAL_DB_NAME = DATABASE_NAME

@pytest.fixture(scope="session", autouse=True)
def setup_test_database_once_article():
    import lib.db.connection
    lib.db.connection.DATABASE_NAME = TEST_DB_NAME
    db_path = os.path.join(BASE_DIR, TEST_DB_NAME)
    
    # Schema setup should ideally be handled by a single session-scoped fixture
    # in conftest.py or one of the test files that runs first.
    # Assuming it's handled or this is compatible.
    if not os.path.exists(db_path): # Only create schema if DB file doesn't exist
        conn = sqlite3.connect(TEST_DB_NAME)
        conn.row_factory = sqlite3.Row
        schema_path = os.path.join(BASE_DIR, 'lib', 'db', 'schema.sql')
        with open(schema_path, 'r') as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        conn.commit()
        conn.close()
        print(f"Test database schema created for Article tests: {TEST_DB_NAME}")

    yield

    # Teardown (optional, if main session fixture handles it)
    # if os.path.exists(db_path) and lib.db.connection.DATABASE_NAME == TEST_DB_NAME:
    #     os.remove(db_path)
    lib.db.connection.DATABASE_NAME = ORIGINAL_DB_NAME


@pytest.fixture(autouse=True)
def setup_test_database_article(setup_test_database_once_article):
    """Clears data from tables before each test function for Article tests."""
    conn = get_db_connection() # Connects to TEST_DB_NAME
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles")
            cursor.execute("DELETE FROM authors") # Clear authors and magazines too for FK constraints
            cursor.execute("DELETE FROM magazines")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='authors'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='magazines'")
            conn.commit()
        finally:
            conn.close()
    else:
        raise Exception("Failed to connect to test database for Article test cleanup.")


class TestArticle:
    """Tests for the Article class."""

    @pytest.fixture
    def sample_author_mag(self):
        """Fixture to create a sample author and magazine for article tests."""
        author = Author.create(name="Sample Author")
        magazine = Magazine.create(name="Sample Magazine", category="Samples")
        assert author is not None and author.id is not None
        assert magazine is not None and magazine.id is not None
        return author, magazine

    def test_article_creation_and_save(self, sample_author_mag):
        """Test creating and saving an article."""
        author, magazine = sample_author_mag
        article = Article(title="My Test Article", content="Test content here.",
                          author_id=author.id, magazine_id=magazine.id)
        assert article.id is None
        article.save()
        assert article.id is not None

        fetched_article = Article.get_by_id(article.id)
        assert fetched_article is not None
        assert fetched_article.title == "My Test Article"
        assert fetched_article.content == "Test content here."
        assert fetched_article.author_id == author.id
        assert fetched_article.magazine_id == magazine.id
        assert fetched_article.id == article.id

    def test_article_property_validation(self, sample_author_mag):
        """Test article property validations."""
        author, magazine = sample_author_mag
        
        # Title validation (length: 5-255 chars)
        with pytest.raises(ValueError, match="Article title must be a string between 5 and 255 characters."):
            Article(title="Shrt", content="Valid", author_id=author.id, magazine_id=magazine.id)
        with pytest.raises(ValueError, match="Article title must be a string between 5 and 255 characters."):
            Article(title="L"*256, content="Valid", author_id=author.id, magazine_id=magazine.id)
        
        # ID validation
        with pytest.raises(ValueError, match="Author ID must be an integer."):
            Article(title="Valid Title", content="Valid", author_id="not-an-int", magazine_id=magazine.id)
        with pytest.raises(ValueError, match="Magazine ID must be an integer."):
            Article(title="Valid Title", content="Valid", author_id=author.id, magazine_id="not-an-int")

        # Content validation (must be string)
        with pytest.raises(ValueError, match="Article content must be a string."):
            Article(title="Valid Title", content=123, author_id=author.id, magazine_id=magazine.id)


        art = Article.create("Valid Article Title", "Valid content", author.id, magazine.id)
        assert art is not None
        with pytest.raises(ValueError, match="Article title must be a string between 5 and 255 characters."):
            art.title = "Bad"
        with pytest.raises(ValueError, match="Article content must be a string."):
            art.content = 12345


    def test_article_create_method(self, sample_author_mag):
        """Test the Article.create class method."""
        author, magazine = sample_author_mag
        article = Article.create(title="Created Article", content="Content for created.",
                                 author_id=author.id, magazine_id=magazine.id)
        assert article is not None
        assert article.id is not None
        assert article.title == "Created Article"
        assert article.author_id == author.id
        assert article.magazine_id == magazine.id

        fetched_article = Article.get_by_id(article.id)
        assert fetched_article.title == "Created Article"

    def test_get_all_articles(self, sample_author_mag):
        """Test retrieving all articles."""
        author, magazine = sample_author_mag
        articles_before = Article.get_all()
        assert len(articles_before) == 0

        Article.create("Article One", "Content 1", author.id, magazine.id)
        Article.create("Article Two", "Content 2", author.id, magazine.id)

        articles_after = Article.get_all()
        assert len(articles_after) == 2
        titles = {art.title for art in articles_after}
        assert "Article One" in titles
        assert "Article Two" in titles

    def test_article_deletion(self, sample_author_mag):
        """Test deleting an article."""
        author, magazine = sample_author_mag
        article = Article.create("ToDelete Article", "Content.", author.id, magazine.id)
        article_id = article.id
        assert Article.get_by_id(article_id) is not None

        article.delete()
        assert article.id is None # Should be marked as deleted
        assert Article.get_by_id(article_id) is None

    def test_article_property_setters_update_db(self, sample_author_mag):
        """Test that setting properties updates the database."""
        author, magazine = sample_author_mag
        article = Article.create("Original Title", "Original Content", author.id, magazine.id)
        article_id = article.id
        
        article.title = "Updated Title via Setter"
        article.content = "Updated Content via Setter"
        
        fetched_article = Article.get_by_id(article_id)
        assert fetched_article is not None
        assert fetched_article.title == "Updated Title via Setter"
        assert fetched_article.content == "Updated Content via Setter"

    def test_article_repr(self, sample_author_mag):
        """Test the __repr__ method of Article."""
        author, magazine = sample_author_mag
        article = Article(title="Repr Article", content="", author_id=author.id, magazine_id=magazine.id, id=303)
        expected_repr = f"<Article id=303 title='Repr Article' author_id={author.id} magazine_id={magazine.id}>"
        assert repr(article) == expected_repr
        
        unsaved_article = Article(title="Unsaved", content="", author_id=author.id, magazine_id=magazine.id)
        expected_unsaved_repr = f"<Article id=None title='Unsaved' author_id={author.id} magazine_id={magazine.id}>"
        assert repr(unsaved_article) == expected_unsaved_repr


    def test_article_save_with_invalid_foreign_keys(self):
        """Test saving an article with non-existent author or magazine ID."""
        author_valid = Author.create("Valid Author")
        magazine_valid = Magazine.create("Valid Magazine", "Valid")
        invalid_id = 99999 # Assumed not to exist

        # Invalid author_id
        article1 = Article(title="Test Invalid Author", content="", author_id=invalid_id, magazine_id=magazine_valid.id)
        assert article1.save() is False # Should fail due to _check_foreign_key_exists

        # Invalid magazine_id
        article2 = Article(title="Test Invalid Magazine", content="", author_id=author_valid.id, magazine_id=invalid_id)
        assert article2.save() is False

        # Check that no articles were actually saved with these titles
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE title = ? OR title = ?", 
                       ("Test Invalid Author", "Test Invalid Magazine"))
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 0


    # --- Relationship Property Tests ---

    def test_article_author_property(self, sample_author_mag):
        """Test the article.author property."""
        author, magazine = sample_author_mag
        article = Article.create("Authored Article", "Content", author.id, magazine.id)

        retrieved_author = article.author
        assert retrieved_author is not None
        assert isinstance(retrieved_author, Author)
        assert retrieved_author.id == author.id
        assert retrieved_author.name == author.name

    def test_article_magazine_property(self, sample_author_mag):
        """Test the article.magazine property."""
        author, magazine = sample_author_mag
        article = Article.create("Published Article", "Content", author.id, magazine.id)

        retrieved_magazine = article.magazine
        assert retrieved_magazine is not None
        assert isinstance(retrieved_magazine, Magazine)
        assert retrieved_magazine.id == magazine.id
        assert retrieved_magazine.name == magazine.name

    # --- Class Methods for Finding Articles ---

    def test_find_article_by_title(self, sample_author_mag):
        """Test Article.find_by_title()."""
        author, magazine = sample_author_mag
        Article.create("Unique Search Title", "Content A", author.id, magazine.id)
        Article.create("Another Unique Title", "Content B", author.id, magazine.id)
        Article.create("Searchable Common Title", "Content C", author.id, magazine.id)
        Article.create("Another Searchable Common Title", "Content D", author.id, magazine.id)


        found_unique = Article.find_by_title("Unique Search Title")
        assert len(found_unique) == 1
        assert found_unique[0].content == "Content A"

        found_common = Article.find_by_title("Searchable Common") # Partial match
        assert len(found_common) == 2
        
        found_partial = Article.find_by_title("Title") # Very broad partial match
        # This will depend on exact titles, adjust assertion if needed
        # For the titles above, it should find 4 if "Title" is in all of them.
        # "Unique Search Title", "Another Unique Title", "Searchable Common Title", "Another Searchable Common Title"
        assert len(found_partial) == 4


        assert Article.find_by_title("NonExistentXYZ") == []

    def test_find_articles_by_author_id(self, sample_author_mag):
        """Test Article.find_by_author_id()."""
        author1, mag1 = sample_author_mag
        author2 = Author.create("Second Author")
        mag2 = Magazine.create("Second Magazine", "Other")

        Article.create("Article A1", "", author1.id, mag1.id)
        Article.create("Article A2", "", author1.id, mag2.id)
        Article.create("Article B1", "", author2.id, mag1.id)

        author1_articles = Article.find_by_author_id(author1.id)
        assert len(author1_articles) == 2
        titles_a1 = {art.title for art in author1_articles}
        assert "Article A1" in titles_a1
        assert "Article A2" in titles_a1

        author2_articles = Article.find_by_author_id(author2.id)
        assert len(author2_articles) == 1
        assert author2_articles[0].title == "Article B1"

        assert Article.find_by_author_id(99999) == [] # Non-existent author

    def test_find_articles_by_magazine_id(self, sample_author_mag):
        """Test Article.find_by_magazine_id()."""
        author1, mag1 = sample_author_mag
        author2 = Author.create("Author For Mag Test")
        mag2 = Magazine.create("Magazine Two", "Testing")

        Article.create("Article M1A", "", author1.id, mag1.id) # Mag1
        Article.create("Article M2A", "", author2.id, mag1.id) # Mag1
        Article.create("Article M1B", "", author1.id, mag2.id) # Mag2

        mag1_articles = Article.find_by_magazine_id(mag1.id)
        assert len(mag1_articles) == 2
        titles_m1 = {art.title for art in mag1_articles}
        assert "Article M1A" in titles_m1
        assert "Article M2A" in titles_m1

        mag2_articles = Article.find_by_magazine_id(mag2.id)
        assert len(mag2_articles) == 1
        assert mag2_articles[0].title == "Article M1B"

        assert Article.find_by_magazine_id(88888) == [] # Non-existent magazine
