# lib/models/author.py
from ..db.connection import get_db_connection
# To avoid circular imports, Article and Magazine will be imported within methods if needed
# or type hinted using strings.

class Author:
    """Represents an author in the application."""

    def __init__(self, name, id=None):
        """
        Initializes a new Author instance.

        Args:
            name (str): The name of the author.
            id (int, optional): The ID of the author if it exists in the database. Defaults to None.
        """
        if not isinstance(name, str) or len(name) == 0:
            raise ValueError("Author name must be a non-empty string.")
        self._name = name
        self._id = id # Will be set when saved to DB or fetched from DB

    @property
    def id(self):
        """int: The ID of the author."""
        return self._id

    @property
    def name(self):
        """str: The name of the author."""
        return self._name

    @name.setter
    def name(self, value):
        """
        Sets the name of the author.

        Args:
            value (str): The new name for the author.

        Raises:
            ValueError: If the name is not a non-empty string.
        """
        if not isinstance(value, str) or len(value) == 0:
            raise ValueError("Author name must be a non-empty string.")
        self._name = value
        # If the author has an ID, update in DB as well
        if self._id is not None:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE authors SET name = ? WHERE id = ?", (self._name, self._id))
                    conn.commit()
                except Exception as e:
                    print(f"Error updating author name in DB: {e}")
                finally:
                    conn.close()


    def __repr__(self):
        """
        Returns a string representation of the Author instance.
        """
        return f"<Author id={self.id} name='{self.name}'>"

    def save(self):
        """
        Saves the Author instance to the database.
        If the author already has an ID, it updates the existing record.
        Otherwise, it inserts a new record and updates the instance's ID.
        """
        conn = get_db_connection()
        if not conn:
            print("Failed to save author: Database connection error.")
            return False

        try:
            cursor = conn.cursor()
            if self._id is None: # Insert new author
                cursor.execute("INSERT INTO authors (name) VALUES (?)", (self.name,))
                self._id = cursor.lastrowid # Get the ID of the newly inserted row
            else: # Update existing author
                cursor.execute("UPDATE authors SET name = ? WHERE id = ?", (self.name, self.id))
            conn.commit()
            return True
        except sqlite3.IntegrityError: # Handles UNIQUE constraint violation for name
             print(f"Error: Author with name '{self.name}' already exists.")
             # Optionally, fetch and assign the existing author's ID
             existing_author = Author.find_by_name(self.name)
             if existing_author:
                 self._id = existing_author.id
             return False
        except Exception as e:
            print(f"Error saving author: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def create(cls, name):
        """
        Creates a new Author, saves it to the database, and returns the instance.

        Args:
            name (str): The name of the author.

        Returns:
            Author: The created Author instance, or None if creation failed.
        """
        try:
            author = cls(name)
            if author.save():
                return author
            return None
        except ValueError as ve:
            print(f"Validation error: {ve}")
            return None


    @classmethod
    def get_by_id(cls, author_id):
        """
        Retrieves an author by their ID from the database.

        Args:
            author_id (int): The ID of the author to find.

        Returns:
            Author: An Author instance if found, otherwise None.
        """
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM authors WHERE id = ?", (author_id,))
            row = cursor.fetchone()
            if row:
                return cls(name=row["name"], id=row["id"])
            return None
        except Exception as e:
            print(f"Error finding author by ID: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def find_by_name(cls, name):
        """
        Retrieves an author by their name from the database.

        Args:
            name (str): The name of the author to find.

        Returns:
            Author: An Author instance if found, otherwise None.
        """
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM authors WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return cls(name=row["name"], id=row["id"])
            return None
        except Exception as e:
            print(f"Error finding author by name: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_all(cls):
        """
        Retrieves all authors from the database.

        Returns:
            list[Author]: A list of Author instances, or an empty list if none are found or an error occurs.
        """
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM authors")
            rows = cursor.fetchall()
            return [cls(name=row["name"], id=row["id"]) for row in rows]
        except Exception as e:
            print(f"Error getting all authors: {e}")
            return []
        finally:
            conn.close()

    def delete(self):
        """
        Deletes the author from the database.
        Note: This will also delete associated articles due to ON DELETE CASCADE.
        """
        if self._id is None:
            print("Cannot delete an author that has not been saved.")
            return False

        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM authors WHERE id = ?", (self.id,))
            conn.commit()
            self._id = None # Mark as deleted
            return True
        except Exception as e:
            print(f"Error deleting author: {e}")
            return False
        finally:
            conn.close()

    # --- Relationship Methods ---

    def articles(self):
        """
        Returns a list of all articles written by the author.

        Returns:
            list[Article]: A list of Article instances.
        """
        from .article import Article # Import here to avoid circular dependency
        conn = get_db_connection()
        if not conn or self.id is None:
            return []
        try:
            cursor = conn.cursor()
            # Assuming articles table has author_id, title, content, magazine_id
            cursor.execute("""
                SELECT id, title, content, author_id, magazine_id
                FROM articles
                WHERE author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            # We need the Article class to instantiate these.
            # For now, let's assume Article class takes these args.
            return [Article(id=row["id"], title=row["title"], content=row["content"],
                            author_id=row["author_id"], magazine_id=row["magazine_id"]) for row in rows]
        except Exception as e:
            print(f"Error fetching articles for author {self.name}: {e}")
            return []
        finally:
            conn.close()

    def magazines(self):
        """
        Returns a unique list of magazines the author has contributed to.

        Returns:
            list[Magazine]: A list of Magazine instances.
        """
        from .magazine import Magazine # Import here
        conn = get_db_connection()
        if not conn or self.id is None:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT m.id, m.name, m.category
                FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                WHERE a.author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Magazine(id=row["id"], name=row["name"], category=row["category"]) for row in rows]
        except Exception as e:
            print(f"Error fetching magazines for author {self.name}: {e}")
            return []
        finally:
            conn.close()

    def add_article(self, magazine, title, content=""):
        """
        Creates and inserts a new Article into the database for this author.

        Args:
            magazine (Magazine): The Magazine instance where the article is published.
            title (str): The title of the new article.
            content (str, optional): The content of the article. Defaults to "".

        Returns:
            Article: The newly created Article instance, or None if creation failed.
        """
        from .article import Article # Import here
        if self.id is None:
            print("Author must be saved before adding an article.")
            return None
        if magazine.id is None:
            print("Magazine must be saved before adding an article to it.")
            return None

        try:
            article = Article(title=title, content=content, author_id=self.id, magazine_id=magazine.id)
            if article.save():
                return article
            return None
        except ValueError as ve:
            print(f"Validation error creating article: {ve}")
            return None
        except Exception as e:
            print(f"Error adding article for author {self.name}: {e}")
            return None

    def topic_areas(self):
        """
        Returns a unique list of categories of magazines the author has contributed to.

        Returns:
            list[str]: A list of unique category names. Returns None if no topics or an error.
        """
        if self.id is None:
            return None # Or [] if preferred for consistency

        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT m.category
                FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                WHERE a.author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [row["category"] for row in rows] if rows else []
        except Exception as e:
            print(f"Error fetching topic areas for author {self.name}: {e}")
            return None # Or []
        finally:
            conn.close()

    # --- Static/Class Methods for specific queries ---
    @classmethod
    def author_with_most_articles(cls):
        """
        Finds the author who has written the most articles.

        Returns:
            Author: The Author instance with the most articles, or None if no authors or an error.
        """
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.id, a.name, COUNT(ar.id) as article_count
                FROM authors a
                JOIN articles ar ON a.id = ar.author_id
                GROUP BY a.id, a.name
                ORDER BY article_count DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return cls(id=row["id"], name=row["name"])
            return None # No authors or no articles
        except Exception as e:
            print(f"Error finding author with most articles: {e}")
            return None
        finally:
            conn.close()

# Example of transaction handling (can be a static method or a free function)
def add_author_with_articles(author_name, articles_data):
    """
    Add an author and their articles in a single transaction.
    articles_data: list of dicts with 'title', 'content', and 'magazine_id' keys.
    """
    from .article import Article # Import here
    conn = get_db_connection()
    if not conn:
        print("Transaction failed: Database connection error.")
        return False

    try:
        # Using conn.execute for DDL/DML that don't return rows,
        # or for context manager style transactions if sqlite3 version supports it well.
        # For explicit control, use cursor.
        cursor = conn.cursor()
        conn.execute("BEGIN TRANSACTION") # Start transaction

        # Insert author
        cursor.execute(
            "INSERT INTO authors (name) VALUES (?)",
            (author_name,)
        )
        author_id = cursor.lastrowid
        if not author_id: # Check if author insertion was successful
            raise Exception("Failed to insert author.")

        # Insert articles
        for article_info in articles_data:
            if not all(k in article_info for k in ['title', 'magazine_id']):
                raise ValueError("Article data missing 'title' or 'magazine_id'.")

            # Validate magazine_id exists (optional, but good practice)
            cursor.execute("SELECT id FROM magazines WHERE id = ?", (article_info['magazine_id'],))
            if not cursor.fetchone():
                raise ValueError(f"Magazine with ID {article_info['magazine_id']} not found.")

            cursor.execute(
                "INSERT INTO articles (title, content, author_id, magazine_id) VALUES (?, ?, ?, ?)",
                (article_info['title'], article_info.get('content', ''), author_id, article_info['magazine_id'])
            )
        conn.execute("COMMIT") # Commit transaction
        print(f"Author '{author_name}' and their articles added successfully.")
        return Author(name=author_name, id=author_id) # Return the created author instance
    except ValueError as ve:
        if conn: conn.execute("ROLLBACK") # Rollback transaction
        print(f"Transaction validation error: {ve}")
        return False
    except sqlite3.IntegrityError as ie: # e.g. author name unique constraint
        if conn: conn.execute("ROLLBACK")
        print(f"Transaction integrity error: {ie}. Author '{author_name}' might already exist.")
        return False
    except Exception as e:
        if conn: conn.execute("ROLLBACK") # Rollback transaction
        print(f"Transaction failed: {e}")
        return False
    finally:
        if conn:
            conn.close()
