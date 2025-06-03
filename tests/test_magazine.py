# tests/test_magazine.py
import pytest
import sqlite3
import os

# Add project root to sys.path
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from lib.db.connection import get_db_connection, DATABASE_NAME
from lib.models.magazine import Magazine
from lib.models.author import Author # Needed for relationship tests
from lib.models.article import Article # Needed for relationship tests

# Use the same test DB setup as test_author.py
TEST_DB_NAME = 'test_articles.db' # Should match test_author
ORIGINAL_DB_NAME = DATABASE_NAME

@pytest.fixture(scope="session", autouse=True)
def setup_test_database_once_magazine():
    import lib.db.connection
    lib.db.connection.DATABASE_NAME = TEST_DB_NAME
    db_path = os.path.join(BASE_DIR, TEST_DB_NAME)
    if os.path.exists(db_path) and lib.db.connection.DATABASE_NAME == TEST_DB_NAME : # only delete if we are sure it's our test db
        # This check is a bit redundant if the test runner ensures isolation,
        # but good for safety if tests are run in unusual ways.
        # The primary schema setup should happen once per session.
        # If test_author.py's session fixture already ran, this might be duplicative
        # or could conflict. Pytest handles fixture dependencies; ensure they align.
        # For simplicity, assuming this might be the first session fixture hit or
        # that they are compatible.
        # A single session-scoped DB setup in a conftest.py is often cleaner.
        pass # Schema setup should be handled by a single session-scoped fixture

    # If schema isn't guaranteed by another session fixture:
    conn = sqlite3.connect(TEST_DB_NAME)
    conn.row_factory = sqlite3.Row
    schema_path = os.path.join(BASE_DIR, 'lib', 'db', 'schema.sql')
    if not os.path.exists(db_path): # Only create schema if DB file doesn't exist
        with open(schema_path, 'r') as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        conn.commit()
        print(f"Test database schema created for Magazine tests: {TEST_DB_NAME}")
    conn.close()

    yield

    # Teardown (optional, if the main session fixture handles it)
    # if os.path.exists(db_path) and lib.db.connection.DATABASE_NAME == TEST_DB_NAME:
    #     os.remove(db_path)
    lib.db.connection.DATABASE_NAME = ORIGINAL_DB_NAME


@pytest.fixture(autouse=True)
def setup_test_database_magazine(setup_test_database_once_magazine):
    """Clears data from tables before each test function for Magazine tests."""
    conn = get_db_connection() # Connects to TEST_DB_NAME
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles")
            cursor.execute("DELETE FROM authors")
            cursor.execute("DELETE FROM magazines")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='articles'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='authors'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='magazines'")
            conn.commit()
        finally:
            conn.close()
    else:
        raise Exception("Failed to connect to test database for Magazine test cleanup.")


class TestMagazine:
    """Tests for the Magazine class."""

    def test_magazine_creation_and_save(self):
        """Test creating and saving a magazine."""
        magazine = Magazine(name="Tech Weekly", category="Technology")
        assert magazine.id is None
        magazine.save()
        assert magazine.id is not None

        fetched_magazine = Magazine.get_by_id(magazine.id)
        assert fetched_magazine is not None
        assert fetched_magazine.name == "Tech Weekly"
        assert fetched_magazine.category == "Technology"
        assert fetched_magazine.id == magazine.id

    def test_magazine_property_validation(self):
        """Test magazine property validations."""
        with pytest.raises(ValueError, match="Magazine name must be a non-empty string."):
            Magazine(name="", category="Valid Category")
        with pytest.raises(ValueError, match="Magazine category must be a non-empty string."):
            Magazine(name="Valid Name", category="")
        
        # Length constraints (example, adjust if your model has different ones)
        with pytest.raises(ValueError, match="Magazine name must be between 2 and 100 characters."):
            Magazine(name="T", category="Tech") # Too short
        with pytest.raises(ValueError, match="Magazine name must be between 2 and 100 characters."):
            Magazine(name="T"*101, category="Tech") # Too long
        
        with pytest.raises(ValueError, match="Magazine category must be between 2 and 50 characters."):
            Magazine(name="Tech Weekly", category="T") # Too short
        with pytest.raises(ValueError, match="Magazine category must be between 2 and 50 characters."):
            Magazine(name="Tech Weekly", category="T"*51) # Too long


        mag = Magazine.create("Valid Mag", "Valid Cat")
        assert mag is not None
        with pytest.raises(ValueError, match="Magazine name must be a string between 2 and 100 characters."):
            mag.name = "N"
        with pytest.raises(ValueError, match="Magazine category must be a string between 2 and 50 characters."):
            mag.category = "C"


    def test_magazine_create_method(self):
        """Test the Magazine.create class method."""
        magazine = Magazine.create(name="Science Monthly", category="Science")
        assert magazine is not None
        assert magazine.id is not None
        assert magazine.name == "Science Monthly"
        assert magazine.category == "Science"

        fetched_magazine = Magazine.get_by_id(magazine.id)
        assert fetched_magazine.name == "Science Monthly"

    def test_find_magazine_by_name_and_category(self):
        """Test finding magazines by name and category."""
        Magazine.create(name="FindMe Mag", category="Search")
        Magazine.create(name="FindMe Mag", category="Another") # Same name, diff category

        found_by_name = Magazine.find_by_name("FindMe Mag")
        assert len(found_by_name) == 2

        found_by_cat = Magazine.find_by_category("Search")
        assert len(found_by_cat) == 1
        assert found_by_cat[0].name == "FindMe Mag"

        assert Magazine.find_by_name("Non Existent Mag") == []
        assert Magazine.find_by_category("Non Existent Cat") == []

    def test_get_all_magazines(self):
        """Test retrieving all magazines."""
        mags_before = Magazine.get_all()
        assert len(mags_before) == 0

        Magazine.create(name="Mag A", category="Cat A")
        Magazine.create(name="Mag B", category="Cat B")

        mags_after = Magazine.get_all()
        assert len(mags_after) == 2
        names = {mag.name for mag in mags_after}
        assert "Mag A" in names
        assert "Mag B" in names

    def test_magazine_deletion(self):
        """Test deleting a magazine."""
        magazine = Magazine.create(name="Old News", category="Obsolete")
        magazine_id = magazine.id
        assert Magazine.get_by_id(magazine_id) is not None

        magazine.delete()
        assert magazine.id is None # Should be marked as deleted
        assert Magazine.get_by_id(magazine_id) is None

    def test_magazine_property_setters_update_db(self):
        """Test that setting properties updates the database."""
        magazine = Magazine.create("Original Name", "Original Category")
        magazine_id = magazine.id
        
        magazine.name = "Updated Name"
        magazine.category = "Updated Category"
        
        fetched_magazine = Magazine.get_by_id(magazine_id)
        assert fetched_magazine is not None
        assert fetched_magazine.name == "Updated Name"
        assert fetched_magazine.category == "Updated Category"

    def test_magazine_repr(self):
        """Test the __repr__ method of Magazine."""
        mag = Magazine(name="Rep Mag", category="Repr Cat", id=202)
        assert repr(mag) == "<Magazine id=202 name='Rep Mag' category='Repr Cat'>"
        
        unsaved_mag = Magazine(name="Unsaved Mag", category="Unsaved Cat")
        assert repr(unsaved_mag) == "<Magazine id=None name='Unsaved Mag' category='Unsaved Cat'>"

    # --- Relationship Tests ---

    def test_magazine_articles_empty(self):
        """Test magazine.articles() when there are no articles."""
        magazine = Magazine.create("Empty Mag", "General")
        assert magazine.articles() == []

    def test_magazine_contributors_empty(self):
        """Test magazine.contributors() when no one contributed."""
        magazine = Magazine.create("Unpopular Mag", "Niche")
        assert magazine.contributors() == []

    def test_magazine_articles_and_contributors_populated(self):
        """Test magazine.articles() and magazine.contributors() with data."""
        mag1 = Magazine.create("Popular Monthly", "General")
        author1 = Author.create("Writer Alpha")
        author2 = Author.create("Writer Beta")

        # Articles for mag1
        article1 = Article.create("Hello World in Python", "Content...", author1.id, mag1.id)
        article2 = Article.create("Data Science Trends", "Content...", author2.id, mag1.id)
        article3 = Article.create("Advanced Python Tips", "Content...", author1.id, mag1.id) # Alpha again

        # Check articles
        mag1_articles = mag1.articles()
        assert len(mag1_articles) == 3
        titles = {art.title for art in mag1_articles}
        assert "Hello World in Python" in titles
        assert "Data Science Trends" in titles
        assert "Advanced Python Tips" in titles

        # Check contributors (should be unique)
        mag1_contributors = mag1.contributors()
        assert len(mag1_contributors) == 2
        contrib_names = {auth.name for auth in mag1_contributors}
        assert "Writer Alpha" in contrib_names
        assert "Writer Beta" in contrib_names

    def test_magazine_article_titles(self):
        """Test magazine.article_titles()."""
        mag = Magazine.create("Title Test Mag", "Tests")
        author = Author.create("Test Author")

        Article.create("Title One", "", author.id, mag.id)
        Article.create("Title Two", "", author.id, mag.id)

        titles = mag.article_titles()
        assert titles is not None
        assert len(titles) == 2
        assert "Title One" in titles
        assert "Title Two" in titles

        empty_mag = Magazine.create("No Articles Mag", "Empty")
        assert empty_mag.article_titles() == []

    def test_magazine_contributing_authors_more_than_two_articles(self):
        """Test magazine.contributing_authors() for authors with > 2 articles."""
        mag = Magazine.create("Frequent Contributors Mag", "Collaboration")
        author_ prolific = Author.create("Prolific Pete")
        author_regular = Author.create("Regular Rita")
        author_once = Author.create("Once-off Oscar")

        # Prolific Pete: 3 articles
        Article.create("Pete Article 1", "", author_prolific.id, mag.id)
        Article.create("Pete Article 2", "", author_prolific.id, mag.id)
        Article.create("Pete Article 3", "", author_prolific.id, mag.id)

        # Regular Rita: 2 articles
        Article.create("Rita Article 1", "", author_regular.id, mag.id)
        Article.create("Rita Article 2", "", author_regular.id, mag.id)

        # Once-off Oscar: 1 article
        Article.create("Oscar Article 1", "", author_once.id, mag.id)

        heavy_contributors = mag.contributing_authors()
        assert len(heavy_contributors) == 1
        assert heavy_contributors[0].name == "Prolific Pete"
        assert heavy_contributors[0].id == author_prolific.id

    def test_magazines_with_articles_by_min_authors(self):
        """Test Magazine.magazines_with_articles_by_min_authors()."""
        mag1 = Magazine.create("Solo Mag", "Single Author Focus") # 1 author
        mag2 = Magazine.create("Duo Digest", "Two Authors") # 2 authors
        mag3 = Magazine.create("Trio Tribune", "Three Authors") # 3 authors
        mag_empty = Magazine.create("Empty Mag", "No Articles")

        author_a = Author.create("Author A")
        author_b = Author.create("Author B")
        author_c = Author.create("Author C")

        # Mag1: Author A only
        Article.create("A's Story 1", "", author_a.id, mag1.id)
        # Mag2: Author A and B
        Article.create("A's Story 2", "", author_a.id, mag2.id)
        Article.create("B's Story 1", "", author_b.id, mag2.id)
        # Mag3: Author A, B, and C
        Article.create("A's Story 3", "", author_a.id, mag3.id)
        Article.create("B's Story 2", "", author_b.id, mag3.id)
        Article.create("C's Story 1", "", author_c.id, mag3.id)

        # Test for >= 2 authors
        mags_min_2_authors = Magazine.magazines_with_articles_by_min_authors(min_authors=2)
        assert len(mags_min_2_authors) == 2
        names_min_2 = {m.name for m in mags_min_2_authors}
        assert "Duo Digest" in names_min_2
        assert "Trio Tribune" in names_min_2

        # Test for >= 3 authors
        mags_min_3_authors = Magazine.magazines_with_articles_by_min_authors(min_authors=3)
        assert len(mags_min_3_authors) == 1
        assert mags_min_3_authors[0].name == "Trio Tribune"

        # Test for >= 1 author (should include mag1, mag2, mag3)
        mags_min_1_author = Magazine.magazines_with_articles_by_min_authors(min_authors=1)
        assert len(mags_min_1_author) == 3


    def test_article_counts_per_magazine(self):
        """Test Magazine.article_counts_per_magazine()."""
        mag_a = Magazine.create("Alpha Mag", "A") # 2 articles
        mag_b = Magazine.create("Bravo Mag", "B") # 1 article
        mag_c = Magazine.create("Charlie Mag", "C") # 0 articles
        author = Author.create("Any Author")

        Article.create("Article 1A", "", author.id, mag_a.id)
        Article.create("Article 2A", "", author.id, mag_a.id)
        Article.create("Article 1B", "", author.id, mag_b.id)

        counts = Magazine.article_counts_per_magazine()
        assert counts is not None
        assert len(counts) == 3 # All magazines should be listed

        counts_dict = {row['magazine_name']: row['article_count'] for row in counts}
        assert counts_dict["Alpha Mag"] == 2
        assert counts_dict["Bravo Mag"] == 1
        assert counts_dict["Charlie Mag"] == 0

    def test_top_publisher(self):
        """Test Magazine.top_publisher()."""
        mag_pop = Magazine.create("Popular Choice", "General") # 3 articles
        mag_mid = Magazine.create("Medium Read", "Niche")     # 2 articles
        mag_new = Magazine.create("Newbie News", "Startups")  # 1 article
        author = Author.create("Busy Author")

        Article.create("Pop Art 1", "", author.id, mag_pop.id)
        Article.create("Pop Art 2", "", author.id, mag_pop.id)
        Article.create("Pop Art 3", "", author.id, mag_pop.id)

        Article.create("Med Art 1", "", author.id, mag_mid.id)
        Article.create("Med Art 2", "", author.id, mag_mid.id)

        Article.create("New Art 1", "", author.id, mag_new.id)

        top_mag = Magazine.top_publisher()
        assert top_mag is not None
        assert top_mag.id == mag_pop.id
        assert top_mag.name == "Popular Choice"

        # Test with no articles
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articles") # Clear articles
        cursor.execute("DELETE FROM magazines") # Clear magazines
        conn.commit()
        Magazine.create("Lonely Mag", "Empty") # Exists but no articles
        assert Magazine.top_publisher() is None
        conn.close()
