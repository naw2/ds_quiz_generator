"""generate_practice.py — Connect weak-topic analysis to Claude question generation.

This script does 4 things, in order:
1. Ask for a student name
2. Look up their weak topics from the quiz_history.db database
3. For each weak topic, call Claude to generate 2 new practice questions
4. Save all generated questions to a JSON file

Now analyze.py and generate_question.py actually talk to each other!
"""

import sqlite3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Reuse our question generator (no duplicate code!)
from generate_question import generate_question

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
load_dotenv()
DB_FILE = "quiz_history.db"
WEAK_THRESHOLD = 70  # percent — below this, a topic counts as "weak"
QUESTIONS_PER_TOPIC = 2  # how many new questions to generate per weak topic


# ---------------------------------------------------------
# STEP 1: Find weak topics (same logic as analyze.py)
# ---------------------------------------------------------
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


def find_weak_topics(student_name):
    """Return a list of topic names where accuracy is below WEAK_THRESHOLD."""
    breakdown = get_topic_breakdown(student_name)

    if not breakdown:
        return None  # no history at all

    weak = []
    for topic, total, correct in breakdown:
        accuracy = (correct / total) * 100
        if accuracy < WEAK_THRESHOLD:
            weak.append(topic)

    return weak


# ---------------------------------------------------------
# STEP 2: Save generated questions to a file
# ---------------------------------------------------------
def save_practice_questions(student_name, questions):
    """Save the generated questions to a JSON file, one per student per run."""
    # Create a safe filename from the student name + timestamp
    safe_name = student_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"practice_{safe_name}_{timestamp}.json"

    output = {
        "student": student_name,
        "generated_on": datetime.now().isoformat(),
        "total_questions": len(questions),
        "questions": questions,
    }

    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    return filename


# ---------------------------------------------------------
# STEP 3: Main — tie everything together
# ---------------------------------------------------------
def generate_practice():
    """Full pipeline: find weak topics → generate questions → save to file."""

    print("=" * 55)
    print("   🎯 PERSONALIZED PRACTICE QUESTION GENERATOR")
    print("=" * 55)

    # --- Get student name ---
    student_name = input("\nEnter student name: ").strip()

    # --- Find weak topics ---
    print(f"\n🔍 Looking up quiz history for '{student_name}'...")
    weak_topics = find_weak_topics(student_name)

    if weak_topics is None:
        print(f"\n❌ No quiz history found for '{student_name}'.")
        print("   Make sure they've taken the quiz first (run quiz.py).")
        return

    if not weak_topics:
        print(f"\n🎉 '{student_name}' has NO weak topics (everything ≥ {WEAK_THRESHOLD}%).")
        print("   No practice questions needed — great job!")
        return

    print(f"\n📌 Found {len(weak_topics)} weak topic(s): {', '.join(weak_topics)}")
    print(f"   (Topics with accuracy below {WEAK_THRESHOLD}%)\n")

    # --- Generate questions for each weak topic ---
    all_questions = []
    for topic in weak_topics:
        print(f"🤖 Generating {QUESTIONS_PER_TOPIC} question(s) for: {topic}...")
        for _ in range(QUESTIONS_PER_TOPIC):
            try:
                new_q = generate_question(topic)
                all_questions.append(new_q)
                print(f"   ✅ Created: {new_q['question'][:60]}...")
            except Exception as e:
                print(f"   ⚠️  Failed to generate a question for {topic}: {e}")

    if not all_questions:
        print("\n❌ Could not generate any questions. Check your API key and connection.")
        return

    # --- Save to file ---
    print(f"\n💾 Saving {len(all_questions)} question(s) to a file...")
    filename = save_practice_questions(student_name, all_questions)

    # --- Summary ---
    print()
    print("=" * 55)
    print("   ✅ DONE!")
    print("=" * 55)
    print(f"   Student:        {student_name}")
    print(f"   Weak topics:    {', '.join(weak_topics)}")
    print(f"   Questions made: {len(all_questions)}")
    print(f"   Saved to:       {filename}")
    print()
    print("   📝 Tip: You can now add these questions to quiz.py")
    print("          or use them for manual practice.")


if __name__ == "__main__":
    generate_practice()
