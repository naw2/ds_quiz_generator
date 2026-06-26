"""database.py — Shared database functions for the Quiz Generator.

Every file that needs to read or write quiz_history.db should import
from this module instead of creating its own connection logic.

This keeps the schema in ONE place and makes changes easy.
"""

import sqlite3
from datetime import datetime

DB_FILE = "quiz_history.db"


def get_connection():
    """Return a connection to the quiz database."""
    return sqlite3.connect(DB_FILE)


def setup_database():
    """Create the quiz_results table if it doesn't exist.
    Also adds the 'difficulty' column if missing (migration for old data).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            topic TEXT,
            question TEXT,
            is_correct INTEGER,
            difficulty TEXT DEFAULT 'beginner',
            timestamp TEXT
        )
    """)

    # Migration: add 'difficulty' column to existing tables
    cursor.execute("PRAGMA table_info(quiz_results)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'difficulty' not in columns:
        cursor.execute("ALTER TABLE quiz_results ADD COLUMN difficulty TEXT DEFAULT 'beginner'")

    conn.commit()
    conn.close()


def save_result(student_name, topic, question, is_correct, difficulty='beginner'):
    """Save ONE answer (one question) into the database.

    Args:
        student_name: The student's name
        topic: The question topic (e.g. 'lists', 'numpy')
        question: The full question text
        is_correct: True/False or 1/0
        difficulty: 'beginner', 'intermediate', or 'advanced'
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_results (student_name, topic, question, is_correct, difficulty, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        student_name,
        topic,
        question,
        1 if is_correct else 0,
        difficulty,
        datetime.now().isoformat(),
    ))

    conn.commit()
    conn.close()
