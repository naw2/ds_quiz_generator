"""quiz.py — A simple multiple-choice quiz for Data Science beginners.

This version adds:
- A "topic" label on every question (so we can track weak areas later)
- A SQLite database that saves every answer (correct or not)
"""

import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# STEP A: Database setup
# ---------------------------------------------------------
DB_FILE = "quiz_history.db"


def setup_database():
    """Create the quiz_results table if it doesn't already exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            topic TEXT,
            question TEXT,
            is_correct INTEGER,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_result(student_name, topic, question, is_correct):
    """Save ONE answer (one question) into the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quiz_results (student_name, topic, question, is_correct, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        student_name,
        topic,
        question,
        1 if is_correct else 0,
        datetime.now().isoformat(),
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# STEP B: Quiz questions (now with a "topic" on each one)
# ---------------------------------------------------------
questions = [
    {
        "question": "What is the correct way to create a list in Python?",
        "options": {
            "A": "list = (1, 2, 3)",
            "B": "list = [1, 2, 3]",
            "C": "list = {1, 2, 3}",
            "D": "list = <1, 2, 3>",
        },
        "answer": "B",
        "topic": "lists",
    },
    {
        "question": "Which library is most commonly used for numerical computing in Python?",
        "options": {
            "A": "pandas",
            "B": "matplotlib",
            "C": "numpy",
            "D": "seaborn",
        },
        "answer": "C",
        "topic": "numpy",
    },
    {
        "question": "What does the len() function do?",
        "options": {
            "A": "Returns the length of a list, string, or other collection",
            "B": "Converts a number to a string",
            "C": "Rounds a number to the nearest integer",
            "D": "Opens a file for reading",
        },
        "answer": "A",
        "topic": "built_in_functions",
    },
    {
        "question": "What is the correct syntax to define a function in Python?",
        "options": {
            "A": "function my_func():",
            "B": "def my_func():",
            "C": "define my_func():",
            "D": "func my_func():",
        },
        "answer": "B",
        "topic": "functions",
    },
    {
        "question": "What data type is the value True in Python?",
        "options": {
            "A": "int",
            "B": "str",
            "C": "bool",
            "D": "float",
        },
        "answer": "C",
        "topic": "data_types",
    },
]


# ---------------------------------------------------------
# STEP C: Run the quiz
# ---------------------------------------------------------
def run_quiz():
    """Run the quiz: ask questions, check answers, save each result, show score."""

    setup_database()

    student_name = input("Enter your name: ").strip()

    score = 0
    total = len(questions)
    print("=" * 50)
    print("       DATA SCIENCE BASICS — PYTHON QUIZ")
    print("=" * 50)
    print(f"\nThere are {total} questions. Type A, B, C, or D to answer.\n")

    for i, q in enumerate(questions, start=1):
        print(f"Question {i}: {q['question']}")
        for letter, text in q["options"].items():
            print(f"   {letter}. {text}")

        while True:
            user_answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            if user_answer in ("A", "B", "C", "D"):
                break
            print("Invalid input. Please type A, B, C, or D.")

        is_correct = (user_answer == q["answer"])

        save_result(student_name, q["topic"], q["question"], is_correct)

        if is_correct:
            print("   ✅ Correct!\n")
            score += 1
        else:
            print(f"   ❌ Incorrect. The answer was {q['answer']}.\n")

    print("=" * 50)
    print(f"           FINAL SCORE: {score}/{total}")
    percentage = (score / total) * 100
    print(f"           That's {percentage:.0f}%")

    if percentage == 100:
        print("           Perfect score! 🎉")
    elif percentage >= 80:
        print("           Great job! 🌟")
    elif percentage >= 60:
        print("           Good effort! Keep practicing.")
    else:
        print("           Keep studying — you'll get it!")
    print("=" * 50)
    print(f"\n(Your results have been saved to {DB_FILE})")


if __name__ == "__main__":
    run_quiz()
