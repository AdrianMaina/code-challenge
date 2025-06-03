# lib/models/magazine.py
import sqlite3
from ..db.connection import get_db_connection
# from .author import Author # Avoid direct import at module level if Author imports Magazine
# from .article import Article # Avoid direct import at module level if Article imports Magazine

class Magazine:
    """Represents a magazine in the application."""

    def __init__(self, name, category, id=None):
        """
        Initializes a new Magazine instance.

        Args:
            name (str): The name of the magazine.
            category (str): The category of the magazine.
            id (int, optional): The ID of the magazine if it exists in the database. Defaults to None.
        """
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError("Magazine name must be a non-empty string.")
        if not isinstance(category, str) or len(category) == 0:
            raise ValueError("Magazine category must be a non-empty string.")
        # Basic validation for name and category length (optional)
        if not (2 <= len(name) <= 100): # Example length constraints
            raise ValueError("Magazine name must be between 2 and 100 characters.")
        if not (2 <= len(category) <= 50): # Example length constraints
             raise ValueError("Magazine category must be between 2 and 50 characters.")


        self._name = name
        self._category = category
        self._id = id

    @property
    def id(self):
        """int: The ID of the magazine."""
        return self._id

    @property
    def name(self):
        """str: The name of the magazine."""
        return self._name

    @name.setter
    def name(self, value):
        """Sets the name of the magazine."""
        if not isinstance(value, str) or not (2 <= len(value) <= 100):
            raise ValueError("Magazine name must be a string between 2 and 100 characters.")
        self._name = value
        if self._id is not None: self._update_field_in_db('name', value)

    @property
    def category(self):
        """str: The category of the magazine."""
        return self._category

    @category.setter
    def category(self, value):
        """Sets the category of the magazine."""
        if not isinstance(value, str) or not (2 <= len(value) <= 50):
            raise ValueError("Magazine category must be a string between 2 and 50 characters.")
        self._category = value
        if self._id is not None: self._update_field_in_db('category', value)

    def _update_field_in_db(self, field_name, value):
        """Helper to update a single field in the database."""
        conn = get_db_connection()
        if conn and self._id is not None:
            try:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE magazines SET {field_name} = ? WHERE id = ?", (value, self._id))
                conn.commit()
            except Exception as e:
                print(f"Error updating magazine {field_name} in DB: {e}")
            finally:
                conn.close()


    def __repr__(self):
        """Returns a string representation of the Magazine instance."""
        return f"<Magazine id={self.id} name='{self.name}' category='{self.category}'>"

    def save(self):
        """
        Saves the Magazine instance to the database.
        If the magazine already has an ID, it updates the existing record.
        Otherwise, it inserts a new record and updates the instance's ID.
        """
        conn = get_db_connection()
        if not conn:
            print("Failed to save magazine: Database connection error.")
            return False
        try:
            cursor = conn.cursor()
            if self._id is None:
                cursor.execute(
                    "INSERT INTO magazines (name, category) VALUES (?, ?)",
                    (self.name, self.category)
                )
                self._id = cursor.lastrowid
            else:
                cursor.execute(
                    "UPDATE magazines SET name = ?, category = ? WHERE id = ?",
                    (self.name, self.category, self.id)
                )
            conn.commit()
            return True
        except sqlite3.IntegrityError as e: # Example: if (name, category) had a UNIQUE constraint
            print(f"Error: Magazine with name '{self.name}' and category '{self.category}' might already exist or another integrity constraint violated: {e}")
            # Optionally, fetch and assign the existing magazine's ID if applicable
            # existing_magazine = Magazine.find_by_name_and_category(self.name, self.category)
            # if existing_magazine:
            # self._id = existing_magazine.id
            return False
        except Exception as e:
            print(f"Error saving magazine: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def create(cls, name, category):
        """
        Creates a new Magazine, saves it to the database, and returns the instance.

        Args:
            name (str): The name of the magazine.
            category (str): The category of the magazine.

        Returns:
            Magazine: The created Magazine instance, or None if creation failed.
        """
        try:
            magazine = cls(name, category)
            if magazine.save():
                return magazine
            return None
        except ValueError as ve:
            print(f"Validation error: {ve}")
            return None


    @classmethod
    def get_by_id(cls, magazine_id):
        """Retrieves a magazine by its ID."""
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category FROM magazines WHERE id = ?", (magazine_id,))
            row = cursor.fetchone()
            return cls(id=row["id"], name=row["name"], category=row["category"]) if row else None
        except Exception as e:
            print(f"Error finding magazine by ID: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def find_by_name(cls, name):
        """Retrieves magazines by name (can return multiple if names are not unique)."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category FROM magazines WHERE name = ?", (name,))
            rows = cursor.fetchall()
            return [cls(id=row["id"], name=row["name"], category=row["category"]) for row in rows]
        except Exception as e:
            print(f"Error finding magazine by name: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def find_by_category(cls, category):
        """Retrieves magazines by category."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category FROM magazines WHERE category = ?", (category,))
            rows = cursor.fetchall()
            return [cls(id=row["id"], name=row["name"], category=row["category"]) for row in rows]
        except Exception as e:
            print(f"Error finding magazine by category: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_all(cls):
        """Retrieves all magazines."""
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, category FROM magazines")
            rows = cursor.fetchall()
            return [cls(id=row["id"], name=row["name"], category=row["category"]) for row in rows]
        except Exception as e:
            print(f"Error getting all magazines: {e}")
            return []
        finally:
            conn.close()

    def delete(self):
        """Deletes the magazine from the database."""
        if self._id is None:
            print("Cannot delete a magazine that has not been saved.")
            return False
        conn = get_db_connection()
        if not conn: return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM magazines WHERE id = ?", (self.id,))
            conn.commit()
            self._id = None # Mark as deleted
            return True
        except Exception as e:
            print(f"Error deleting magazine: {e}")
            return False
        finally:
            conn.close()

    # --- Relationship Methods ---

    def articles(self):
        """Returns a list of all articles published in the magazine."""
        from .article import Article # Import here
        if self.id is None: return []
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, content, author_id, magazine_id
                FROM articles
                WHERE magazine_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Article(id=row["id"], title=row["title"], content=row["content"],
                            author_id=row["author_id"], magazine_id=row["magazine_id"]) for row in rows]
        except Exception as e:
            print(f"Error fetching articles for magazine {self.name}: {e}")
            return []
        finally:
            conn.close()

    def contributors(self):
        """Returns a unique list of authors who have written for this magazine."""
        from .author import Author # Import here
        if self.id is None: return []
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT au.id, au.name
                FROM authors au
                JOIN articles ar ON au.id = ar.author_id
                WHERE ar.magazine_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Author(id=row["id"], name=row["name"]) for row in rows]
        except Exception as e:
            print(f"Error fetching contributors for magazine {self.name}: {e}")
            return []
        finally:
            conn.close()

    def article_titles(self):
        """Returns a list of titles of all articles in the magazine."""
        if self.id is None: return None # Or []

        conn = get_db_connection()
        if not conn: return None # Or []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM articles WHERE magazine_id = ?", (self.id,))
            rows = cursor.fetchall()
            return [row["title"] for row in rows] if rows else []
        except Exception as e:
            print(f"Error fetching article titles for magazine {self.name}: {e}")
            return None # Or []
        finally:
            conn.close()

    def contributing_authors(self):
        """
        Returns a list of authors who have written more than 2 articles for this magazine.
        If no authors meet the criteria, returns an empty list.
        """
        from .author import Author # Import here
        if self.id is None: return []

        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT au.id, au.name, COUNT(ar.id) as article_count
                FROM authors au
                JOIN articles ar ON au.id = ar.author_id
                WHERE ar.magazine_id = ?
                GROUP BY au.id, au.name
                HAVING article_count > 2
            """, (self.id,))
            rows = cursor.fetchall()
            return [Author(id=row["id"], name=row["name"]) for row in rows]
        except Exception as e:
            print(f"Error fetching contributing authors for magazine {self.name}: {e}")
            return []
        finally:
            conn.close()

    # --- Static/Class Methods for specific queries ---

    @classmethod
    def magazines_with_articles_by_min_authors(cls, min_authors=2):
        """
        Finds magazines with articles by at least a minimum number of different authors.

        Args:
            min_authors (int): The minimum number of different authors. Default is 2.

        Returns:
            list[Magazine]: A list of Magazine instances.
        """
        conn = get_db_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT m.id, m.name, m.category, COUNT(DISTINCT a.author_id) as author_count
                FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id, m.name, m.category
                HAVING author_count >= ?
            """, (min_authors,))
            rows = cursor.fetchall()
            return [cls(id=row["id"], name=row["name"], category=row["category"]) for row in rows]
        except Exception as e:
            print(f"Error finding magazines with at least {min_authors} authors: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def article_counts_per_magazine(cls):
        """
        Counts the number of articles in each magazine.

        Returns:
            list[dict]: A list of dictionaries, each with 'magazine_name', 'magazine_category', and 'article_count'.
                        Returns None if an error occurs.
        """
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.name as magazine_name, m.category as magazine_category, COUNT(a.id) as article_count
                FROM magazines m
                LEFT JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id, m.name, m.category
                ORDER BY m.name
            """)
            # Using fetchall() which returns a list of Row objects (like dicts)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error counting articles per magazine: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def top_publisher(cls):
        """
        Class method to find the magazine with the most articles.

        Returns:
            Magazine: The Magazine instance with the most articles, or None if no magazines or an error.
        """
        conn = get_db_connection()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.name, m.category, COUNT(a.id) as article_count
                FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id, m.name, m.category
                ORDER BY article_count DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return cls(id=row["id"], name=row["name"], category=row["category"])
            return None # No magazines or no articles
        except Exception as e:
            print(f"Error finding top publisher: {e}")
            return None
        finally:
            conn.close()
