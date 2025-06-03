# Object Relations Code Challenge - Articles

This project models the relationship between Authors, Articles, and Magazines using Python and a SQL database (SQLite).

## Project Overview

The system allows for:
- Authors to write many Articles.
- Magazines to publish many Articles.
- Articles to belong to one Author and one Magazine.
- A many-to-many relationship between Authors and Magazines through Articles.

## Features
- Database schema for Authors, Articles, and Magazines.
- Python classes (`Author`, `Article`, `Magazine`) to interact with the database using raw SQL queries.
- Methods for creating, retrieving, and managing relationships between these entities.
- Database seeding for testing purposes.
- Pytest tests to ensure functionality and data integrity.
- Transaction management for database operations.

## Project Structure


code-challenge/
├── lib/
│   ├── models/
│   │   ├── init.py
│   │   ├── author.py
│   │   ├── article.py
│   │   └── magazine.py
│   ├── db/
│   │   ├── init.py
│   │   ├── connection.py
│   │   ├── schema.sql
│   │   └── seed.py
│   ├── controllers/
│   │   └── init.py
│   ├── debug.py
│   └── init.py
├── tests/
│   ├── init.py
│   ├── test_author.py
│   ├── test_article.py
│   └── test_magazine.py
├── scripts/
│   ├── setup_db.py
│   └── run_queries.py
├── .gitignore
└── README.md


## Setup and Installation

Follow the setup instructions provided in the main challenge description (Pipenv or venv).

### Database Setup (SQLite)
The project is configured to use SQLite. The database file will be named `articles.db`.

1.  **Initialize the database schema:**
    ```bash
    python scripts/setup_db.py
    ```
2.  **Seed the database with initial data (optional but recommended for testing):**
    After running `setup_db.py`, you can run `python lib/db/seed.py` directly if it's designed to be executable, or integrate its logic into `setup_db.py`.

## Running Tests
To run the tests, navigate to the root directory of the project and execute:
```bash
pytest

Interactive Debugging
To explore the models and database interactively:

python lib/debug.py

Running Example Queries
(If scripts/run_queries.py is implemented)

python scripts/run_queries.py
