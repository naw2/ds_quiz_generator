# Quiz Generator — Project Guide for Claude Code

## Project Overview
This is a Personalized Quiz Generator for data science students.
The app gives a Python quiz, tracks which topics a student gets wrong,
and will eventually generate NEW questions targeting their weak topics
(e.g. pandas, numpy, lists, loops) using the Claude API.

Built by: naw2

## Tech Stack
- Language: Python 3.12
- Storage: SQLite (quiz_history.db)
- AI: Claude API via teacher-provided proxy (proxy.vibecode.tours, model: mimo-v2.5-pro)
- UI: Streamlit web app (app.py) + command line scripts

## Current Status (as of 2026-06-18)

### What we have built so far:

| File | Purpose |
|------|---------|
| `quiz.py` | Main quiz: 5 questions with topic tags, asks student name, saves every answer to SQLite |
| `quiz_backup.py` | Original quiz before topic tags + database (kept as reference) |
| `analyze.py` | Reads quiz_history.db and shows weak topics (accuracy below 70%) for a student |
| `generate_question.py` | Calls Claude API to create a new multiple-choice question for a given topic |
| `generate_practice.py` | Bridge: finds weak topics → calls Claude → saves generated questions to a JSON file |
| `practice_quiz.py` | Full end-to-end: finds weak topics, generates fresh questions on the fly, runs a quiz, saves results back to DB |
| `app.py` | Streamlit web UI — run the quiz, check progress, and practice in a browser |

### Claude Code tools we've set up:

| Tool type | Name | File | What it does |
|-----------|------|------|-------------|
| CLAUDE.md | (this file) | `CLAUDE.md` | Project instructions — always loaded |
| Skill | quiz-manager | `.claude/skills/quiz-manager/SKILL.md` | Handbook: tells Claude which script does what |
| Agent | quiz-reporter | `.claude/agents/quiz-reporter.md` | Helper: reads DB and writes classroom reports |
| MCP Server | quiz-manager | `mcp_server.py` | Direct DB access: 5 tools Claude can call directly |

### MCP Server Tools
When the MCP server is connected, Claude can call these tools directly:
- `list_students` — Show every student and their overall score
- `get_student_report` — Topic-by-topic breakdown for one student
- `get_class_summary` — Bird's-eye classroom overview
- `get_weak_topics` — Which topics a student needs practice with (below 70%)
- `get_recent_activity` — Most recent quiz answers

The MCP server auto-connects via `.mcp.json` — no manual setup needed. When you open this project in Claude Code, the server is ready to use.

### Key design decisions:
- Topic tags on every question (lists, numpy, built_in_functions, functions, data_types)
- SQLite database chosen (quiz_history.db) with 34 recorded answers from 4 students
- Claude API connected via proxy.vibecode.tours (NOT the Anthropic SDK — uses plain HTTP via `requests`)
- Practice questions saved as JSON files (e.g. practice_khin_2026-06-17_180942.json)
- Weak topic threshold = accuracy below 70%
- Every Claude-generated question uses a random seed to ensure variety between runs

## Roadmap (in order — do not skip ahead)
1. [DONE] Basic quiz that scores the user.
2. [DONE] Add a "topic" tag to each question + save quiz results to a file after each run.
3. [DONE] Analyze saved results to find weak topics.
4. [DONE] Use Claude API to generate new questions for weak topics.
5. [DONE] Build a simple Streamlit UI.

## Working Style — IMPORTANT
- I am a beginner with Claude Code, CLAUDE.md, and AI agent concepts.
- Explain EVERY step in simple English before and after writing code.
- No unexplained jargon. If you must use a technical term, define it
  in plain language the first time.
- Do not introduce advanced tools (subagents, custom skills, plugins)
  unless I specifically ask. Keep it simple until I say otherwise.
- This project will be used 3 ways: for my own learning, for my
  students to use, and as a portfolio project — so code should be
  clean and well-commented, not just "quick and dirty".
