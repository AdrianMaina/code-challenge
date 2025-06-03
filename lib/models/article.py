# lib/models/article.py
import sqlite3
from ..db.connection import get_db_connection
# from .author import Author # Avoid direct import at module level
# from .magazine import Magazine # Avoid direct import at module level

class Article:
    """Represents an article in the application."""

    def __init__(self, title, author_id, magazine_id, content="", id=None):
        """
        Initializes a new Article instance.

        Args:
            title (str): The title of the article. Must be between 5 and 150 chars.
            author_id (int): The ID of the author of this article.
            magazine_id (int): The ID of the magazine publishing this article.
            content (str, optional): The content of the article. Defaults to "".
            id (int, optional): The ID of the article if it exists in the database. Defaults to None.
        """
        if not isinstance(title, str) or not (5 <= len(title) <= 255): # Adjusted length constraint
            raise ValueError("Article title must be a string between 5 and 255 characters.")
        if not isinstance(author_id, int):
            raise ValueError("Author ID must be an integer.")
        if not isinstance(magazine_id, int):
            raise ValueError("Magazine ID must be an integer.")
        if not isinstance(content, str):
            raise ValueError("Article content must be a string.")


        self._title = title
        self._content = content
        self._author_id = author_id
        self._magazine_id = magazine_id
        self._id = id
        # Properties for author and magazine objects will be lazy-loaded
        self._author_instance = None
        self._magazine_instance = None


    @property
    def id(self):
        """int: The ID of the article."""
        return self._id

    @property
    def title(self):
        """str: The title of the article."""
        return self._title

    @title.setter
    def title(self, value):
        """Sets the title of the article."""
        if not isinstance(value, str) or not (5 <= len(value) <= 255):
            raise ValueError("Article title must be a string between 5 and 255 characters.")
        self._title = value
        if self._id is not None: self._update_field_in_db('title', value)


    @property
    def content(self):
        """str: The content of the article."""
        return self._content

    @content.setter
    def content(self, value):
        """Sets the content of the article."""
        if not isinstance(value, str):
            raise ValueError("Article content must be a string.")
        self._content = value
        if self._id is not None: self._update_field_in_db('content', value)

    @property
    def author_id(self):
        """int: The ID of the author of this article."""
        return self._author_id

    # author_id should generally not be changed after creation,
    # as it defines a core relationship. If it needs to change,
    # it might be better to delete and recreate the article,
    # or handle it with a specific method that ensures data integrity.

    @property
    def magazine_id(self):
        """int: The ID of the magazine publishing this article."""
        return self._magazine_id

    # magazine_id, similar to author_id, should generally not be changed lightly.

    def _update_field_in_db(self, field_name, value):
        """Helper to update a single field in the database."""
        conn = get_db_connection()
        if conn and self._id is not None:
            try:
                cursor = conn.cursor()
                # Ensure field_name is safe if it were dynamic (here it's controlled)
                cursor.execute(f"UPDATE articles SET {field_name} = ? WHERE id = ?", (value, self._id))
                conn.commit()
            except Exception as e:
                print(f"Error updating article {field_name} in DB: {e}")
            finally:
                conn.close()

    def __repr__(self):
        """Returns a string representation of the Article instance."""
        return f"<Article id={self.id} title='{self.title}' author_id={self.author_id} magazine_id={self.magazine_id}>"

    def save(self):
        """
        Saves the Article instance to the database.
        If the article already has an ID, it updates the existing record.
        Otherwise, it inserts a new record and updates the instance's ID.
        """
        conn = get_db_connection()
        if not conn:
            print("Failed to save article: Database connection error.")
            return False

        # Validate foreign keys before saving (optional, but good for data integrity)
        # This check should ideally be more robust or handled by database constraints.
        if not self._check_foreign_key_exists("authors", self.author_id):
            print(f"Error: Author with ID {self.author_id} does not exist. Cannot save article.")
            return False
        if not self._check_foreign_key_exists("magazines", self.magazine_id):
            print(f"Error: Magazine with ID {self.magazine_id} does not exist. Cannot save article.")
            return False

        try:
            cursor = conn.cursor()
            if self._id is None:
                cursor.execute(
                    "INSERT INTO articles (title, content, author_id, magazine_id) VALUES (?, ?, ?, ?)",
                    (self.title, self.content, self.author_id, self.magazine_id)
                )
                self._id = cursor.lastrowid
            else:
                cursor.execute(
                    "UPDATE articles SET title = ?, content = ?, author_id = ?, magazine_id = ? WHERE id = ?",
                    (self.title, self.content, self.author_id, self.magazine_id, self.id)
                )
            conn.commit()
            return True
        except sqlite3.IntegrityError as e: # Foreign key constraint might fail here too
            print(f"Database integrity error saving article: {e}")
            # This could be due to author_id or magazine_id not existing if not checked beforehand
            # or other constraints.
            return False
        except Exception as e:
            print(f"Error saving article: {e}")
            return False
        finally:
            conn.close()

    def _check_foreign_key_exists(self, table_name, record_id):
        """Helper to check if a foreign key exists in the referenced table."""
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # Sanitize table_name if it were from user input, but here it's controlled.
            cursor.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (record_id,))
            return cursor.fetchone() is not None
        except Exception:
            return False # Assume non-existent on error
        finally:
            if conn: conn.close()


    @classmethod
    def create(cls, title, content, author_id, magazine_id):
        """
        Creates a new Article, saves it to the database, and returns the instance.

        Args:
            title (str): The title of the article.
            content (str): The content of the article.
            author_id (int): The ID of the author.
            magazine_id (int): The ID of the magazine.

        Returns:
            Article: The created Article instance, or None if creation failed.
        """
        try:
            article = cls(title=title, content=content, author_id=author_id, magazine_id=magazine_id)
            if article.save():
                return article
            return None
        except ValueError as ve:
            print(f"Validation error: {ve}")
            return None


    @classmethod
    def get_by_id(cls, article_id):
        """Retrieves an article by its ID."""
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, author_id, magazine_id FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return cls(id=row["id"], title=row["title"], content=row["content"],
                       author_id=row["author_id"], magazine_id=row["magazine_id"]) if row else None
        except Exception as e:
            print(f"Error finding article by ID: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_all(cls):
        """Retrieves all articles."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, content, author_id, magazine_id FROM articles")
            rows = cursor.fetchall()
            return [cls(id=row["id"], title=row["title"], content=row["content"],
                        author_id=row["author_id"], magazine_id=row["magazine_id"]) for row in rows]
        except Exception as e:
            print(f"Error getting all articles: {e}")
            return []
        finally:
            conn.close()

    def delete(self):
        """Deletes the article from the database."""
        if self._id is None:
            print("Cannot delete an article that has not been saved.")
            return False
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM articles WHERE id = ?", (self.id,))
            conn.commit()
            self._id = None # Mark as deleted
            return True
        except Exception as e:
            print(f"Error deleting article: {e}")
            return False
        finally:
            conn.close()

    # --- Relationship Properties ---

    @property
    def author(self):
        """
        Retrieves the Author instance for this article.
        Lazy-loads the author information.
        """
        from .author import Author # Import here to avoid circular dependency
        if self._author_instance is None and self.author_id is not None:
            self._author_instance = Author.get_by_id(self.author_id)
        return self._author_instance

    @property
    def magazine(self):
        """
        Retrieves the Magazine instance for this article.
        Lazy-loads the magazine information.
        """
        from .magazine import Magazine # Import here
        if self._magazine_instance is None and self.magazine_id is not None:
            self._magazine_instance = Magazine.get_by_id(self.magazine_id)
        return self._magazine_instance

    # --- Static/Class Methods for specific queries ---

    @classmethod
    def find_by_title(cls, title_query):
        """
        Finds articles by a title (can be partial match using LIKE).

        Args:
            title_query (str): The title or part of the title to search for.

        Returns:
            list[Article]: A list of matching Article instances.
        """
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE title LIKE ?", (f"%{title_query}%",))
            rows = cursor.fetchall()
            return [cls(**row) for row in rows] # Assumes column names match __init__ params
        except Exception as e:
            print(f"Error finding articles by title: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def find_by_author_id(cls, author_id):
        """Finds all articles by a specific author ID."""
        return cls._find_by_foreign_key('author_id', author_id)

    @classmethod
    def find_by_magazine_id(cls, magazine_id):
        """Finds all articles by a specific magazine ID."""
        return cls._find_by_foreign_key('magazine_id', magazine_id)

    @classmethod
    def _find_by_foreign_key(cls, key_name, key_id):
        """Helper to find articles by a foreign key (author_id or magazine_id)."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            # Ensure key_name is safe if it were dynamic (here it's controlled)
            cursor.execute(f"SELECT id, title, content, author_id, magazine_id FROM articles WHERE {key_name} = ?", (key_id,))
            rows = cursor.fetchall()
            return [cls(id=r["id"], title=r["title"], content=r["content"],
                        author_id=r["author_id"], magazine_id=r["magazine_id"]) for r in rows]
        except Exception as e:
            print(f"Error finding articles by {key_name}: {e}")
            return []
        finally:
            conn.close()
