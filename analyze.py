"""analyze.py — Find a student's weak topics from their quiz history.

This script reads the quiz_history.db database (created by quiz.py)
and reports, for one student, which topics they need more practice on.

"Weak topic" = accuracy below 70% (our chosen threshold).
"""

import sqlite3

DB_FILE = "quiz_history.db"
WEAK_THRESHOLD = 70  # percent — below this, a topic counts as "weak"


def get_topic_breakdown(student_name):
    """Return a list of (topic, total_attempts, correct_attempts) for one student."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic,
               COUNT(*) AS total_attempts,
               SUM(is_correct) AS correct_attempts
        FROM quiz_results
        WHERE student_name = ?
        GROUP BY topic
    """, (student_name,))

    results = cursor.fetchall()
    conn.close()
    return results


def analyze_student(student_name):
    """Print a full weak-topic report for one student."""

    breakdown = get_topic_breakdown(student_name)

    if not breakdown:
        print(f"No quiz history found for '{student_name}'.")
        print("Make sure the name matches exactly what was typed during the quiz.")
        return

    print("=" * 55)
    print(f"   TOPIC REPORT FOR: {student_name}")
    print("=" * 55)

    weak_topics = []

    for topic, total, correct in breakdown:
        accuracy = (correct / total) * 100
        status = "✅ OK" if accuracy >= WEAK_THRESHOLD else "⚠️  WEAK"

        if accuracy < WEAK_THRESHOLD:
            weak_topics.append(topic)

        print(f"{topic:20s} | {correct}/{total} correct | {accuracy:5.1f}% | {status}")

    print("=" * 55)

    if weak_topics:
        print(f"\n📌 Weak topics (below {WEAK_THRESHOLD}%): {', '.join(weak_topics)}")
        print("   -> These are the topics future practice questions should target.")
    else:
        print(f"\n🎉 No weak topics! Everything is above {WEAK_THRESHOLD}%.")


if __name__ == "__main__":
    name = input("Enter student name to analyze: ").strip()
    analyze_student(name)
