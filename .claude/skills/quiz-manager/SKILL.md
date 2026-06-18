---
name: quiz-manager
description: Run the Python quiz, analyze student results, generate practice questions, or run a personalized practice quiz. Use this whenever the user wants to quiz a student, check weak topics, create practice material, or run personalized quizzes — basically anything involving the quiz scripts in this project.
---

# Quiz Manager

This skill covers all four scripts in the Quiz Generator project.
The project helps data science students practice Python — it gives quizzes,
tracks which topics they get wrong, and generates new questions for their weak areas.

## Project files (always in the project root)

| File | What it does |
|------|-------------|
| `quiz.py` | Main 5-question quiz — saves every answer to SQLite |
| `analyze.py` | Reads the database and shows which topics a student is weak at |
| `generate_practice.py` | Finds weak topics, calls Claude API, saves new questions to a JSON file |
| `practice_quiz.py` | Finds weak topics, generates fresh questions, runs them as a quiz, saves results |
| `quiz_history.db` | SQLite database with all quiz answers |

## Database structure

The `quiz_history.db` file has one table called `quiz_results`:

| Column | What it stores | Example |
|--------|---------------|---------|
| `student_name` | Name the student typed | "khin" |
| `topic` | Topic tag | "lists", "numpy", "functions" |
| `question` | Full question text | "What is the correct way to..." |
| `is_correct` | 1 = right, 0 = wrong | 0 |
| `timestamp` | When they answered | "2026-06-17T11:38:02" |

To check what's in the database, use Python (not the sqlite3 CLI, which may not be installed):
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('quiz_history.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM quiz_results ORDER BY id')
for row in cursor.fetchall():
    print(row)
conn.close()
"
```

## How to run each script

### 1. Main quiz (`quiz.py`)
```bash
cd <project-root> && python3 quiz.py
```
The user needs to type their name and answers interactively. Claude cannot answer quiz questions for the user — just tell them to run it themselves and report back.

### 2. Analyze a student (`analyze.py`)
```bash
cd <project-root> && python3 analyze.py
```
This is interactive — it asks for the student name. The output shows a table with each topic, the score, and flags topics below 70% accuracy as "WEAK".

### 3. Generate practice questions (`generate_practice.py`)
```bash
cd <project-root> && python3 generate_practice.py
```
This calls the Claude API (via proxy.vibecode.tours) to create new questions. Important:
- It needs the `.env` file with API credentials
- It retries up to 3 times if the proxy is flaky
- Output is a JSON file like `practice_khin_2026-06-18_172926.json`
- It generates 2 questions per weak topic by default

### 4. Run a personalized practice quiz (`practice_quiz.py`)
```bash
cd <project-root> && python3 practice_quiz.py
```
This does everything in one go: finds weak topics → generates fresh questions via Claude → runs them as a quiz → saves answers back to the database. Students should run `quiz.py` first so they have history to analyze.

## Key settings (stored in `.env`)

```
ANTHROPIC_BASE_URL=https://proxy.vibecode.tours
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_MODEL=mimo-v2.5-pro
```

The Claude API is called using plain HTTP (the `requests` library), NOT the Anthropic SDK,
because the teacher's proxy expects a different authentication method than what the SDK sends.

## Weak topic rule

A topic is "weak" if the student got less than 70% of questions correct.
This threshold is set at the top of `analyze.py`, `generate_practice.py`, and `practice_quiz.py`.
If you change it, update all three files.

## The 5 core topics

The current question bank covers these topics:
- `lists` — creating and slicing Python lists
- `numpy` — the numerical computing library
- `built_in_functions` — functions like `len()`, `zip()`, `enumerate()`
- `functions` — how to define functions with `def`
- `data_types` — int, float, str, bool, tuple

## When the user asks for help

If something goes wrong, check these common issues in order:
1. Is the `.env` file present and has valid credentials? (for any script that calls Claude)
2. Is `quiz_history.db` present? (for analyze/generate/practice scripts)
3. Does the student name match exactly? (names are case-sensitive — "Khin" ≠ "khin")
4. Is the proxy responding? (it sometimes returns 502 errors — the scripts retry automatically)
