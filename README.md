# 🎯 Personalized Quiz Generator

A Python quiz app that tracks student performance and uses AI to generate fresh practice questions targeting weak areas.

An AI-powered quiz app that tracks student performance, finds weak topics, and generates personalized practice questions using the Claude API.

**🌐 Live App: [https://dsquizgenerator-selht4jqurewdvmusqxkvg.streamlit.app/](https://dsquizgenerator-selht4jqurewdvmusqxkvg.streamlit.app/)**

Built for data science students learning Python basics.

## What It Does

1. **Takes a quiz** — 5 multiple-choice questions on Python fundamentals
2. **Tracks results** — every answer is saved to a SQLite database
3. **Finds weak topics** — analyzes which topics a student struggles with (below 70% accuracy)
4. **Generates new questions** — uses the Claude API to create fresh questions for weak topics
5. **Runs practice quizzes** — personalized quizzes with AI-generated questions, results saved back to track improvement

## Topics Covered

- Lists
- NumPy
- Built-in functions
- Functions
- Data types

## Project Files

| File | What It Does |
|------|--------------|
| `quiz.py` | Main quiz — 5 questions, saves every answer to SQLite |
| `analyze.py` | Reads quiz history and shows weak topics for a student |
| `generate_question.py` | Calls Claude API to create a new question for any topic |
| `generate_practice.py` | Finds weak topics, generates questions, saves to JSON |
| `practice_quiz.py` | Full practice quiz — finds weak topics, generates fresh questions on the fly, saves results |
| `app.py` | **Streamlit web UI** — run the quiz, check progress, and practice in a browser |

## How to Run

### Prerequisites

- Python 3.12+
- `requests` library (for Claude API calls)

```bash
pip install requests python-dotenv streamlit
```

### Run the Web UI (Recommended)

```bash
streamlit run app.py
```

Opens in your browser at `http://localhost:8501`. From there you can:
- Take the quiz
- See your progress with charts
- Practice with AI-generated questions

### Run the Main Quiz (Terminal)

```bash
python3 quiz.py
```

You'll be asked for your name, then answer 5 questions. Results are saved to `quiz_history.db`.

### Analyze Your Progress

```bash
python3 analyze.py
```

Enter a student name to see accuracy by topic. Topics below 70% are flagged as "weak."

### Take a Practice Quiz (AI-Generated Questions)

```bash
python3 practice_quiz.py
```

This finds your weak topics, generates fresh questions using Claude, and runs a personalized quiz. Every run produces different questions.

### Generate a Single Question

```bash
python3 generate_question.py
```

Creates one new question about a topic (default: lists). Edit the script to change the topic.

## How It Works

### Database

All quiz results are stored in `quiz_history.db` (SQLite). Each row records:
- Student name
- Topic (lists, numpy, etc.)
- The question text
- Whether they got it right
- Timestamp

### AI Question Generation

New questions are generated using the Claude API through a teacher-provided proxy. Each generated question includes:
- A multiple-choice question about the target topic
- 4 options (A, B, C, D)
- The correct answer

A random seed ensures every quiz run produces different questions.

### Weak Topic Detection

A topic is "weak" if the student's accuracy is below 70%. The app reads all past answers from the database and groups them by topic to calculate accuracy.

## Example Session

```
$ python3 quiz.py
Enter your name: Alex

==================================================
       DATA SCIENCE BASICS — PYTHON QUIZ
==================================================

There are 5 questions. Type A, B, C, or D to answer.

Question 1: What is the correct way to create a list in Python?
   A. list = (1, 2, 3)
   B. list = [1, 2, 3]
   C. list = {1, 2, 3}
   D. list = <1, 2, 3>

Your answer (A/B/C/D): B
   ✅ Correct!

...

==================================================
           FINAL SCORE: 4/5
           That's 80%
           Great job! 🌟
==================================================

(Your results have been saved to quiz_history.db)
```

## Tech Stack

- **Python 3.12** — main language
- **Streamlit** — web UI framework
- **SQLite** — stores quiz history (`quiz_history.db`)
- **Claude API** — generates new questions via `proxy.vibecode.tours`
- **requests** — HTTP calls to the API
- **python-dotenv** — loads API keys from environment

## Future Plans

- [x] Streamlit web UI
- [ ] More question topics
- [ ] Student progress charts
