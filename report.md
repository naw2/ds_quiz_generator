# ch-3 Personal Project — Report

github_username: naw2
personal_repo_url: https://github.com/naw2/ds_quiz_generator
project_summary: A personalized Python quiz generator for data science students — tracks weak topics, uses Claude API to generate fresh practice questions, and provides classroom reports via MCP tools.
slides_url: slides/pechakucha-6x20.md
live_app_url: https://dsquizgenerator-selht4jqurewdvmusqxkvg.streamlit.app/

## Methodology
<!-- How you worked: project-based approach + your git workflow (commit as you build). 2-4 sentences. -->

I used a project-based approach: started with a basic command-line quiz (`quiz.py`), saved results to a file, then upgraded to SQLite with topic tags so I could analyze which topics each student gets wrong. Once the data layer was solid, I connected the Claude API to generate new practice questions for weak topics, built the practice quiz loop, and finally added the MCP server so Claude Code can query the database directly. I committed after every working feature — the git history shows incremental, building-block commits rather than one giant dump.

## Evidence — Claude Code usage
<!-- List the ACTUAL paths in your personal repo. The validator checks these exist. -->

- .mcp.json
- .claude/skills/quiz-manager/SKILL.md
- .claude/agents/quiz-reporter.md

### MCP
- path: .mcp.json
- what: The quiz-manager MCP server (`mcp_server.py`) connects Claude directly to the SQLite database via 5 tools: `list_students`, `get_student_report`, `get_class_summary`, `get_weak_topics`, and `get_recent_activity`. Used for classroom reporting — teacher or student can ask Claude natural-language questions like "How is Khin doing in numpy?" and get instant answers from the database without writing SQL.

### Skill
- path: .claude/skills/quiz-manager/SKILL.md
- what: A handbook that teaches Claude Code how to manage all quiz operations — which script does what, how to run each one (`quiz.py`, `analyze.py`, `generate_practice.py`, `practice_quiz.py`), the database schema, `.env` configuration, and common troubleshooting steps. Ensures Claude consistently knows the right command to run for any quiz-related task.

### Agent
- path: .claude/agents/quiz-reporter.md
- what: A specialized subagent that reads `quiz_history.db` and produces a clean, formatted classroom report — per-student performance ranked best to worst, per-topic difficulty ranked hardest to easiest, overall class stats, plus plain-English insight about what needs attention. Runs via the `quiz-reporter` agent type so the teacher can request a report without remembering SQL queries.
