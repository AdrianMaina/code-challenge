-- lib/db/schema.sql

-- Drop tables if they exist to ensure a clean setup
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS magazines;
DROP TABLE IF EXISTS authors;

-- Create the authors table
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Standard for SQLite auto-incrementing PK
    name TEXT NOT NULL UNIQUE -- Assuming author names should be unique
);

-- Create the magazines table
CREATE TABLE IF NOT EXISTS magazines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL
    -- Consider adding a UNIQUE constraint on (name, category) if appropriate
    -- UNIQUE(name, category)
);

-- Create the articles table
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT, -- Added a content field, can be TEXT or BLOB
    author_id INTEGER NOT NULL,
    magazine_id INTEGER NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE, -- If an author is deleted, their articles are also deleted
    FOREIGN KEY (magazine_id) REFERENCES magazines(id) ON DELETE CASCADE -- If a magazine is deleted, its articles are also deleted
);

-- Optional: Add indexes for performance on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_articles_author_id ON articles(author_id);
CREATE INDEX IF NOT EXISTS idx_articles_magazine_id ON articles(magazine_id);
CREATE INDEX IF NOT EXISTS idx_authors_name ON authors(name);
CREATE INDEX IF NOT EXISTS idx_magazines_name ON magazines(name);
CREATE INDEX IF NOT EXISTS idx_magazines_category ON magazines(category);

