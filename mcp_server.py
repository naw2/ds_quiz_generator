"""mcp_server.py — MCP server that lets Claude talk directly to the quiz database.

This server exposes 5 tools that Claude can call:
  1. list_students        — Show every student who's taken a quiz
  2. get_student_report   — Topic-by-topic breakdown for one student
  3. get_class_summary    — Overview of all students and all topics
  4. get_weak_topics      — Which topics a student needs to practice (below 70%)
  5. get_recent_activity  — Most recent quiz results

How to connect this to Claude Code:
  claude mcp add --transport stdio quiz-manager "python3 mcp_server.py"

Or for the whole project (global):
  claude mcp add --transport stdio --scope user quiz-manager "python3 mcp_server.py"
"""

import sqlite3
from pathlib import Path

from fastmcp import FastMCP

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
DB_FILE = Path(__file__).parent / "quiz_history.db"
WEAK_THRESHOLD = 70  # below this percent, a topic is "weak"

mcp = FastMCP(
    name="quiz-manager",
    instructions=(
        "Use list_students first to see who has quiz history. "
        "Then use get_student_report or get_weak_topics to drill into a specific student. "
        "Use get_class_summary for a bird's-eye view of the whole classroom."
    ),
)

# ---------------------------------------------------------
# HELPER — shared database connection logic
# ---------------------------------------------------------
def _query(sql, params=()):
    """Run a SELECT query and return all rows."""
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    return results


# ---------------------------------------------------------
# TOOL 1: list_students
# ---------------------------------------------------------
@mcp.tool(annotations={"readOnlyHint": True})
def list_students() -> str:
    """List all students who have taken a quiz, with their total answers and overall accuracy.

    Call this first to see who is in the database before asking about a specific student."""
    rows = _query("""
        SELECT student_name,
               COUNT(*) AS total,
               SUM(is_correct) AS correct,
               ROUND(SUM(is_correct) * 100.0 / COUNT(*), 1) AS pct
        FROM quiz_results
        GROUP BY student_name
        ORDER BY pct DESC
    """)

    if not rows:
        return "📭 No quiz results in the database yet. Run quiz.py to add some!"

    lines = ["👨‍🎓 STUDENTS (best → needs most help)", "-" * 50]
    for name, total, correct, pct in rows:
        emoji = "🎉" if pct == 100 else "✅" if pct >= 70 else "⚠️"
        lines.append(f"  {name:15s} | {correct}/{total} correct | {pct:5.1f}% {emoji}")

    return "\n".join(lines)


# ---------------------------------------------------------
# TOOL 2: get_student_report
# ---------------------------------------------------------
@mcp.tool(annotations={"readOnlyHint": True})
def get_student_report(student_name: str) -> str:
    """Show a full topic-by-topic breakdown for one student.

    Args:
        student_name: The exact name the student typed during the quiz (case-sensitive).
                      Use list_students first if you're not sure of the spelling.
    """
    rows = _query(
        """
        SELECT topic,
               COUNT(*) AS total,
               SUM(is_correct) AS correct,
               ROUND(SUM(is_correct) * 100.0 / COUNT(*), 1) AS pct
        FROM quiz_results
        WHERE student_name = ?
        GROUP BY topic
        ORDER BY pct ASC
        """,
        (student_name,),
    )

    if not rows:
        return (
            f"❌ No quiz history found for '{student_name}'. "
            f"Check the spelling (names are case-sensitive) or use list_students to see who is in the database."
        )

    lines = [f"📊 TOPIC REPORT: {student_name}", "=" * 50]
    weak_list = []

    for topic, total, correct, pct in rows:
        status = "WEAK ⚠️" if pct < WEAK_THRESHOLD else "OK ✅"
        if pct < WEAK_THRESHOLD:
            weak_list.append(topic)
        lines.append(f"  {topic:20s} | {correct}/{total} correct | {pct:5.1f}% | {status}")

    lines.append("=" * 50)

    if weak_list:
        lines.append(f"\n📌 Weak topics (below {WEAK_THRESHOLD}%): {', '.join(weak_list)}")
        lines.append("   Run generate_practice.py to create practice questions for these.")
    else:
        lines.append(f"\n🎉 No weak topics! Everything is at or above {WEAK_THRESHOLD}%.")

    return "\n".join(lines)


# ---------------------------------------------------------
# TOOL 3: get_class_summary
# ---------------------------------------------------------
@mcp.tool(annotations={"readOnlyHint": True})
def get_class_summary() -> str:
    """Show a bird's-eye view: every student and every topic in one compact table.

    Use this to see how the whole class is doing at a glance."""
    # Per-student
    students = _query("""
        SELECT student_name,
               COUNT(*) AS total,
               SUM(is_correct) AS correct,
               ROUND(SUM(is_correct) * 100.0 / COUNT(*), 1) AS pct
        FROM quiz_results
        GROUP BY student_name
        ORDER BY pct DESC
    """)

    # Per-topic (hardest first)
    topics = _query("""
        SELECT topic,
               COUNT(*) AS total,
               SUM(is_correct) AS correct,
               ROUND(SUM(is_correct) * 100.0 / COUNT(*), 1) AS pct
        FROM quiz_results
        GROUP BY topic
        ORDER BY pct ASC
    """)

    counts = _query("SELECT COUNT(DISTINCT student_name), COUNT(*) FROM quiz_results")
    total_students, total_answers = counts[0]

    lines = [
        "=" * 55,
        "        📊 QUIZ GENERATOR — CLASSROOM REPORT",
        "=" * 55,
        "",
        "👨‍🎓 STUDENT PERFORMANCE (best → needs most help)",
        "-" * 55,
    ]

    for name, total, correct, pct in students:
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        lines.append(f"  {name:15s} {bar} {pct:5.1f}% ({correct}/{total})")

    lines.extend([
        "",
        "📚 TOPIC DIFFICULTY (hardest → easiest)",
        "-" * 55,
    ])

    for topic, total, correct, pct in topics:
        lines.append(f"  {topic:20s} | {correct}/{total} correct | {pct:5.1f}%")

    lines.extend([
        "",
        "📈 OVERALL",
        "-" * 55,
        f"  Total students:           {total_students}",
        f"  Total questions answered: {total_answers}",
        "=" * 55,
    ])

    return "\n".join(lines)


# ---------------------------------------------------------
# TOOL 4: get_weak_topics
# ---------------------------------------------------------
@mcp.tool(annotations={"readOnlyHint": True})
def get_weak_topics(student_name: str) -> str:
    """Return only the weak topics for a student (accuracy below 70%).

    These are the topics that need practice questions.

    Args:
        student_name: Exact name the student used during the quiz."""
    rows = _query(
        """
        SELECT topic,
               COUNT(*) AS total,
               SUM(is_correct) AS correct,
               ROUND(SUM(is_correct) * 100.0 / COUNT(*), 1) AS pct
        FROM quiz_results
        WHERE student_name = ?
        GROUP BY topic
        HAVING pct < ?
        ORDER BY pct ASC
        """,
        (student_name, WEAK_THRESHOLD),
    )

    if not rows:
        # Check if the student exists at all
        exists = _query("SELECT COUNT(*) FROM quiz_results WHERE student_name = ?", (student_name,))[0][0]
        if exists == 0:
            return f"❌ No quiz history found for '{student_name}'. Use list_students to see available names."
        return f"🎉 '{student_name}' has NO weak topics! Every topic is at or above {WEAK_THRESHOLD}%."

    lines = [f"⚠️  WEAK TOPICS FOR: {student_name} (below {WEAK_THRESHOLD}%)", "-" * 50]
    for topic, total, correct, pct in rows:
        lines.append(f"  {topic:20s} | {correct}/{total} correct | {pct:5.1f}%")
    lines.append(f"\n💡 Tip: Run generate_practice.py to create practice questions for {student_name}.")

    return "\n".join(lines)


# ---------------------------------------------------------
# TOOL 5: get_recent_activity
# ---------------------------------------------------------
@mcp.tool(annotations={"readOnlyHint": True})
def get_recent_activity(limit: int = 10) -> str:
    """Show the most recent quiz answers across all students.

    Args:
        limit: How many recent results to show (default 10, max 50)."""
    limit = max(1, min(limit, 50))  # clamp between 1 and 50

    rows = _query(
        """
        SELECT student_name, topic, is_correct, timestamp
        FROM quiz_results
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    if not rows:
        return "📭 No quiz activity yet."

    lines = [f"🕐 {limit} MOST RECENT ANSWERS", "-" * 60]
    for name, topic, correct, ts in rows:
        icon = "✅" if correct else "❌"
        lines.append(f"  {ts} | {name:10s} | {topic:20s} | {icon}")

    return "\n".join(lines)


# ---------------------------------------------------------
# MAIN — start the server
# ---------------------------------------------------------
if __name__ == "__main__":
    # Check that the database exists
    if not DB_FILE.exists():
        print("⚠️  Warning: quiz_history.db not found.")
        print("   Run quiz.py first to create it, then start this server again.")
        print()

    mcp.run(transport="stdio")
