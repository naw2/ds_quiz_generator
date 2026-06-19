---
marp: true
paginate: true
transition: fade
auto-advance: 20
---

# Who's my person?

Beginner-level students learning Python
— non-technical backgrounds (bank staff, university staff, school students)
— names in my pilot data: Khin, Hla, Yin, Mya

---

# Their problem

Students don't know which topics they're weak in until it's too late.

They need **targeted practice**, not random quiz questions —
but writing personalized practice questions by hand takes a teacher too much time.

---

# What I built

An AI-powered quiz system that:
1. Runs a quiz and scores the student
2. Saves results with topic tags to a database
3. Analyzes history to find **weak topics**
4. Uses Claude's API to **generate new practice questions** for those weak topics

---

# How I built it

**MCP** — `mcp_server.py` + `.mcp.json`
→ lets Claude Code query `quiz_history.db` directly (students, topics, scores)

**Skill** — `.claude/skills/quiz-manager/SKILL.md`
→ teaches Claude Code how to manage quiz operations consistently

**Agent** — `.claude/agents/quiz-reporter.md`
→ a dedicated agent for generating reports/summaries from quiz data

---

# Why it matters

Saves teachers hours of manually building practice sets.

Gives every student a question set tailored to their **actual** weak spots —
not generic drills everyone gets the same.

---

# Done checklist

- [x] repo public
- [x] MCP + skill + agent used
- [x] report.md in repo

