# Ch-3 Personal Project — Report

**GitHub username:** naw2
**Personal repo URL:** https://github.com/naw2/ds_quiz_generator
**Project summary:** A personalized Python quiz generator for data science students — tracks weak topics, uses Claude API to generate fresh practice questions, and provides classroom reports via MCP tools.

**Slides URL:** slides/pechakucha-6x20.md


## Methodology

### Evidence — Claude Code usage

Claude Code was used throughout this project to:
- Write and iterate on all Python scripts (`quiz.py`, `analyze.py`, `generate_practice.py`, `practice_quiz.py`)
- Design the SQLite database schema for storing quiz results
- Set up the MCP server for direct database access
- Create custom skills and agents for classroom management
- Debug and fix issues as they came up

### MCP

- **Path:** `.mcp.json`
- **What:** The `quiz-manager` MCP server (`mcp_server.py`) connects Claude directly to the SQLite database. It provides 5 tools:
  - `list_students` — show every student and their overall score
  - `get_student_report` — topic-by-topic breakdown for one student
  - `get_class_summary` — bird's-eye classroom overview
  - `get_weak_topics` — which topics a student needs practice with (below 70% accuracy)
  - `get_recent_activity` — most recent quiz answers
- **Used for:** Querying quiz results without writing SQL by hand — the teacher or student can ask Claude natural-language questions like "How is Khin doing in numpy?" and get instant answers.

### Skill

- **Path:** `.claude/skills/quiz-manager/SKILL.md`
- **What:** A handbook that tells Claude which script does what, how to run each one, the database structure, and common troubleshooting steps. Covers all four scripts (`quiz.py`, `analyze.py`, `generate_practice.py`, `practice_quiz.py`) plus the database and `.env` configuration.

### Agent

- **Path:** `.claude/agents/quiz-reporter.md`
- **What:** A specialized subagent that reads the `quiz_history.db` database and produces a clean, formatted classroom report. It shows per-student performance (ranked best to worst), per-topic difficulty (ranked hardest to easiest), overall class stats, and adds plain-English insight about what needs attention.
