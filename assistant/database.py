import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

class DatabaseManager:
    """
    Handles SQLite persistence for expenses and items.
    """
    def __init__(self, db_path: str = "data/expenses.db"):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Expenses Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    merchant TEXT,
                    date TEXT,
                    stated_total INTEGER,
                    calculated_total INTEGER,
                    insight_score INTEGER,
                    status TEXT,
                    attention_reason TEXT,
                    timestamp TEXT
                )
            """)
            # Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_id INTEGER,
                    name TEXT,
                    price INTEGER,
                    category TEXT,
                    flag BOOLEAN,
                    FOREIGN KEY (expense_id) REFERENCES expenses (id)
                )
            """)
            conn.commit()

    def save_expense(self, data: Dict[str, Any]) -> int:
        """
        Saves a full expense analysis result to the database.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert into expenses
            cursor.execute("""
                INSERT INTO expenses (
                    merchant, date, stated_total, calculated_total, 
                    insight_score, status, attention_reason, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('merchant', 'Unknown'),
                data.get('date', 'Unknown'),
                data.get('stated_total', 0),
                data.get('calculated_total', 0),
                data.get('insight_score', 0),
                data.get('status', 'REVIEW'),
                data.get('attention_reason', ''),
                datetime.now().isoformat()
            ))
            
            expense_id = cursor.lastrowid
            
            # Insert items
            items = data.get('items', [])
            for item in items:
                cursor.execute("""
                    INSERT INTO items (expense_id, name, price, category, flag)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    expense_id,
                    item.get('name', 'Unknown'),
                    item.get('price', 0),
                    item.get('category', 'LAINNYA'),
                    item.get('flag', False)
                ))
            
            conn.commit()
            return expense_id

    def save_goal(self, user_id: str, goal_text: str):
        """Saves a user's financial goal."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    goal_text TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("INSERT INTO goals (user_id, goal_text, timestamp) VALUES (?, ?, ?)",
                         (str(user_id), goal_text, datetime.now().isoformat()))
            conn.commit()

    def get_latest_goal(self, user_id: str) -> str:
        """Fetch the latest goal for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT goal_text FROM goals WHERE user_id = ? ORDER BY id DESC LIMIT 1", (str(user_id),))
                result = cursor.fetchone()
                return result[0] if result else ""
        except sqlite3.OperationalError:
            return ""

    def get_recent_expenses(self, limit: int = 10) -> List[Dict]:
        """Fetch recent expenses for history view."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_monthly_total(self) -> int:
        """Calculate total spending for the current month."""
        current_month = datetime.now().strftime("%Y-%m")
        # Note: This assumes the 'date' extracted from receipt is reliable or uses 'timestamp'
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(calculated_total) FROM expenses WHERE timestamp LIKE ?", (f"{current_month}%",))
            result = cursor.fetchone()[0]
            return result if result else 0
