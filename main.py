import json

from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def load_category_catalog():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_category_selection(category, subcategory):
    catalog = load_category_catalog()

    if category not in catalog:
        allowed_categories = ", ".join(sorted(catalog.keys()))
        raise ValueError(f"Invalid category '{category}'. Allowed categories: {allowed_categories}")

    if not subcategory:
        raise ValueError(f"subcategory is required for category '{category}'")

    allowed_subcategories = catalog[category]
    if subcategory not in allowed_subcategories:
        allowed_subcategories_text = ", ".join(allowed_subcategories)
        raise ValueError(
            f"Invalid subcategory '{subcategory}' for category '{category}'. "
            f"Allowed subcategories: {allowed_subcategories_text}"
        )

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool()
def add_expense(date: str, amount: float, category: str, subcategory: str, note: str = ""):
    '''Add a new expense entry to the database. Claude should infer category and subcategory from the expense details using expense://categories and should not ask the user to provide them.'''
    validate_category_selection(category, subcategory)
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()


@mcp.tool()
def get_categories():
    '''Return the category and subcategory catalog used by Claude to classify expenses.'''
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="http", host = "0.0.0.0", port=8000) # Run the MCP server on all available interfaces at port 8000