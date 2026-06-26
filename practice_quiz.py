"""practice_quiz.py — A personalized quiz that generates NEW questions on the fly
for each student's weak topics.

This script:
1. Asks for a student name and difficulty level
2. Looks up their weak topics from quiz_history.db
3. Generates fresh, random questions via Claude for each weak topic
4. Runs them as a quiz (same format as quiz.py)
5. Saves all answers back to the database (so we track improvement)

Every run creates DIFFERENT questions — Claude generates unique ones each time.
"""

import sqlite3
import json
import random
from datetime import datetime

# Import shared database functions
from database import setup_database, save_result, get_connection, DB_FILE

# Reuse our question generator's call_claude function
from generate_question import call_claude

# ---------------------------------------------------------
# SETUP
# ---------------------------------------------------------
WEAK_THRESHOLD = 70  # percent — below this, a topic counts as "weak"
QUESTIONS_PER_TOPIC = 2  # how many new questions per weak topic
DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]


# ---------------------------------------------------------
# STEP 1: Find weak topics (same logic as analyze.py)
# ---------------------------------------------------------
def find_weak_topics(student_name):
    """Return a list of topic names where accuracy is below WEAK_THRESHOLD."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT topic,
               COUNT(*) AS total_attempts,
               SUM(is_correct) AS correct_attempts
        FROM quiz_results
        WHERE student_name = ?
        GROUP BY topic
    """, (student_name,))

    breakdown = cursor.fetchall()
    conn.close()

    if not breakdown:
        return None  # no history at all

    weak = []
    for topic, total, correct in breakdown:
        accuracy = (correct / total) * 100
        if accuracy < WEAK_THRESHOLD:
            weak.append(topic)

    return weak


# ---------------------------------------------------------
# STEP 2: Generate UNIQUE questions each time
# ---------------------------------------------------------
def generate_unique_question(topic, seed_hint, difficulty='beginner'):
    """Generate ONE new question on a topic.

    seed_hint is a random number used to make Claude produce a
    different question every time (so no two quiz runs are the same).
    """
    difficulty_instructions = {
        'beginner': "Ask about basic syntax, definitions, or simple concepts.",
        'intermediate': "Ask about applying concepts, combining features, or reading code.",
        'advanced': "Ask about edge cases, performance trade-offs, or tricky behavior.",
    }

    diff_instruction = difficulty_instructions.get(difficulty, difficulty_instructions['beginner'])

    prompt = f"""Create one multiple-choice Python question for a data science student.
Topic: {topic}
Difficulty level: {difficulty}

{diff_instruction}

IMPORTANT: Make this question DIFFERENT from typical ones about this topic.
Use this random seed as inspiration for variety: seed-{seed_hint}

Reply with ONLY valid JSON, no other text, no markdown formatting,
in exactly this shape:

{{
  "question": "the question text",
  "options": {{
    "A": "option A text",
    "B": "option B text",
    "C": "option C text",
    "D": "option D text"
  }},
  "answer": "A"
}}

The "answer" must be one of "A", "B", "C", or "D" — whichever option is correct."""

    # Retry up to 3 times — the API sometimes returns truncated JSON
    last_error = None
    for attempt in range(1, 4):
        raw_text = call_claude(prompt)

        # Strip markdown code blocks if Claude wraps the JSON
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            first_newline = raw_text.find("\n")
            if first_newline != -1:
                raw_text = raw_text[first_newline + 1:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        try:
            question_data = json.loads(raw_text)
            question_data["topic"] = topic
            question_data["difficulty"] = difficulty
            return question_data
        except json.JSONDecodeError as e:
            last_error = f"JSON parse error (attempt {attempt}): {e}"
            import time
            time.sleep(1)

    raise RuntimeError(f"Failed to generate valid question after 3 attempts: {last_error}")


# ---------------------------------------------------------
# STEP 3: Run the practice quiz
# ---------------------------------------------------------
def run_practice_quiz():
    """Full pipeline: find weak topics → generate fresh questions → quiz → save."""

    setup_database()

    print("=" * 55)
    print("   🎯 PERSONALIZED PRACTICE QUIZ")
    print("=" * 55)

    # --- Get student name ---
    student_name = input("\nEnter student name: ").strip()

    # --- Choose difficulty ---
    print("\nChoose your difficulty level:")
    print("   1. Beginner     (basic syntax and definitions)")
    print("   2. Intermediate (applying concepts, reading code)")
    print("   3. Advanced     (edge cases, tricky behavior)")

    while True:
        choice = input("\nEnter 1, 2, or 3: ").strip()
        if choice in ("1", "2", "3"):
            break
        print("   Please enter 1, 2, or 3.")

    difficulty = DIFFICULTY_LEVELS[int(choice) - 1]

    # --- Find weak topics ---
    print(f"\n🔍 Checking quiz history for '{student_name}'...")
    weak_topics = find_weak_topics(student_name)

    if weak_topics is None:
        print(f"\n❌ No quiz history found for '{student_name}'.")
        print("   Take the main quiz first (run quiz.py), then come back.")
        return

    if not weak_topics:
        print(f"\n🎉 '{student_name}' has NO weak topics (everything ≥ {WEAK_THRESHOLD}%).")
        print("   No practice needed — great job! Go run the main quiz to challenge yourself.")
        return

    print(f"\n📌 Weak topics: {', '.join(weak_topics)}")
    print(f"🤖 Generating {len(weak_topics) * QUESTIONS_PER_TOPIC} {difficulty} questions just for you...\n")

    # --- Generate fresh questions on the fly ---
    quiz_questions = []
    for topic in weak_topics:
        print(f"   Creating {QUESTIONS_PER_TOPIC} question(s) for: {topic}...")
        for _ in range(QUESTIONS_PER_TOPIC):
            try:
                seed_hint = random.randint(1000, 9999)
                new_q = generate_unique_question(topic, seed_hint, difficulty)
                quiz_questions.append(new_q)
                print(f"   ✅ {new_q['question'][:60]}...")
            except Exception as e:
                print(f"   ⚠️  Failed: {e}")

    if not quiz_questions:
        print("\n❌ Could not generate any questions. Check your API key and connection.")
        return

    # --- Shuffle so topics are mixed up (not all "lists" back-to-back) ---
    random.shuffle(quiz_questions)

    # --- Run the quiz ---
    score = 0
    total = len(quiz_questions)
    print("\n" + "=" * 55)
    print(f"   QUIZ TIME! {total} {difficulty} questions — Type A, B, C, or D")
    print("=" * 55 + "\n")

    for i, q in enumerate(quiz_questions, start=1):
        print(f"Question {i} ({q['topic']}): {q['question']}")
        for letter, text in q["options"].items():
            print(f"   {letter}. {text}")

        while True:
            user_answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            if user_answer in ("A", "B", "C", "D"):
                break
            print("   Invalid input. Please type A, B, C, or D.")

        is_correct = (user_answer == q["answer"])

        # Save this answer to the database (tracks improvement over time!)
        save_result(student_name, q["topic"], q["question"], is_correct, difficulty)

        if is_correct:
            print("   ✅ Correct!\n")
            score += 1
        else:
            print(f"   ❌ Incorrect. The answer was {q['answer']}.\n")

    # --- Show final score ---
    print("=" * 55)
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
    print("=" * 55)
    print(f"\n(Results saved to {DB_FILE})")
    print("Run practice_quiz.py again for fresh questions, or analyze.py to see progress.")


if __name__ == "__main__":
    run_practice_quiz()
