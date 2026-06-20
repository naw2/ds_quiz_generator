"""app.py — Streamlit web UI for the Personalized Quiz Generator.

Run with:  streamlit run app.py

Pages:
  1. Home          — welcome + overview
  2. Take Quiz     — 5-question quiz, saves results to SQLite
  3. My Progress   — topic-by-topic accuracy with charts
  4. Practice Quiz — AI-generated questions for weak topics
"""

import streamlit as st
import sqlite3
import json
import random
from datetime import datetime

# Import helpers from our existing scripts
from quiz import setup_database, save_result, questions
from analyze import get_topic_breakdown, WEAK_THRESHOLD
from generate_question import generate_question

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Quiz Generator",
    page_icon="🎯",
    layout="centered",
)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("🎯 Quiz Generator")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Take Quiz", "My Progress", "Practice Quiz"],
)

# ---------------------------------------------------------
# PAGE: HOME
# ---------------------------------------------------------
if page == "Home":
    st.title("🎯 Personalized Quiz Generator")
    st.write("""
    Welcome! This app helps **data science students** practice Python basics.

    ### How it works
    1. **Take a quiz** — answer 5 questions on Python fundamentals
    2. **See your progress** — find out which topics you're weak in
    3. **Practice** — get fresh AI-generated questions targeting your weak spots

    ### Topics covered
    - Lists
    - NumPy
    - Built-in functions
    - Functions
    - Data types

    👈 **Use the sidebar to get started!**
    """)

# ---------------------------------------------------------
# PAGE: TAKE QUIZ
# ---------------------------------------------------------
elif page == "Take Quiz":
    st.title("📝 Take the Quiz")

    # Initialize session state
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.student_name = ""
        st.session_state.answers = []

    # Step 1: Get student name
    if not st.session_state.quiz_started:
        name = st.text_input("Enter your name:")
        if st.button("Start Quiz"):
            if name.strip():
                st.session_state.student_name = name.strip()
                st.session_state.quiz_started = True
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.answers = []
                setup_database()
                st.rerun()
            else:
                st.warning("Please enter your name first!")

    # Step 2: Show questions one at a time
    elif st.session_state.current_q < len(questions):
        q = questions[st.session_state.current_q]
        q_num = st.session_state.current_q + 1
        total = len(questions)

        st.progress(q_num / total)
        st.subheader(f"Question {q_num} of {total}")
        st.write(f"**{q['question']}**")

        # Radio buttons for options
        options = [f"{letter}. {text}" for letter, text in q["options"].items()]
        choice = st.radio("Choose your answer:", options, key=f"q{q_num}")

        if st.button("Submit Answer"):
            selected_letter = choice[0]  # "A", "B", "C", or "D"
            is_correct = selected_letter == q["answer"]

            # Save to database
            save_result(
                st.session_state.student_name,
                q["topic"],
                q["question"],
                is_correct,
            )

            if is_correct:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Incorrect. The answer was {q['answer']}.")

            st.session_state.answers.append({
                "question": q["question"],
                "topic": q["topic"],
                "selected": selected_letter,
                "correct": q["answer"],
                "is_correct": is_correct,
            })

            st.session_state.current_q += 1
            if st.session_state.current_q < len(questions):
                if st.button("Next Question →"):
                    st.rerun()
            else:
                st.rerun()

    # Step 3: Show final results
    else:
        score = st.session_state.score
        total = len(questions)
        pct = (score / total) * 100

        st.balloons()
        st.subheader("🎉 Quiz Complete!")
        st.metric("Score", f"{score}/{total} ({pct:.0f}%)")

        if pct == 100:
            st.success("Perfect score! 🌟")
        elif pct >= 80:
            st.success("Great job! 🌟")
        elif pct >= 60:
            st.info("Good effort! Keep practicing.")
        else:
            st.warning("Keep studying — you'll get it!")

        # Show breakdown
        st.write("---")
        st.subheader("Your Answers")
        for ans in st.session_state.answers:
            icon = "✅" if ans["is_correct"] else "❌"
            st.write(f"{icon} **{ans['topic']}** — {ans['question'][:60]}...")

        if st.button("Take Quiz Again"):
            st.session_state.quiz_started = False
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.answers = []
            st.rerun()

# ---------------------------------------------------------
# PAGE: MY PROGRESS
# ---------------------------------------------------------
elif page == "My Progress":
    st.title("📊 My Progress")

    name = st.text_input("Enter student name:")

    if st.button("Check Progress"):
        if not name.strip():
            st.warning("Please enter a student name.")
        else:
            setup_database()
            breakdown = get_topic_breakdown(name.strip())

            if not breakdown:
                st.warning(f"No quiz history found for '{name.strip()}'.")
                st.write("Take the quiz first!")
            else:
            # Build a table
            st.subheader(f"Topic Report for {name.strip()}")

            data = []
            weak_topics = []
            for topic, total, correct in breakdown:
                accuracy = round((correct / total) * 100, 1)
                status = "✅ OK" if accuracy >= WEAK_THRESHOLD else "⚠️ Weak"
                if accuracy < WEAK_THRESHOLD:
                    weak_topics.append(topic)
                data.append({
                    "Topic": topic,
                    "Correct": correct,
                    "Total": total,
                    "Accuracy %": accuracy,
                    "Status": status,
                })

            st.dataframe(data, use_container_width=True)

            # Bar chart
            st.subheader("Accuracy by Topic")
            chart_data = {row["Topic"]: row["Accuracy %"] for row in data}
            st.bar_chart(chart_data)

            # Weak topics alert
            if weak_topics:
                st.error(f"⚠️ Weak topics (below {WEAK_THRESHOLD}%): **{', '.join(weak_topics)}**")
                st.write("Go to **Practice Quiz** to work on these!")
            else:
                st.success(f"🎉 All topics above {WEAK_THRESHOLD}%! Great job!")

# ---------------------------------------------------------
# PAGE: PRACTICE QUIZ
# ---------------------------------------------------------
elif page == "Practice Quiz":
    st.title("🎯 Practice Quiz (AI-Generated)")

    # Initialize session state for practice
    if "practice_started" not in st.session_state:
        st.session_state.practice_started = False
        st.session_state.practice_questions = []
        st.session_state.practice_current = 0
        st.session_state.practice_score = 0
        st.session_state.practice_name = ""
        st.session_state.practice_answers = []

    if not st.session_state.practice_started:
        name = st.text_input("Enter your name:")

        if st.button("Find My Weak Topics"):
            if not name.strip():
                st.warning("Please enter your name.")
            else:
                setup_database()
                from practice_quiz import find_weak_topics
                weak = find_weak_topics(name.strip())

                if weak is None:
                    st.warning(f"No quiz history for '{name.strip()}'. Take the main quiz first!")
                elif not weak:
                    st.success(f"🎉 No weak topics! You're doing great!")
                else:
                    st.session_state.practice_name = name.strip()
                    st.session_state.practice_weak_topics = weak
                    st.rerun()

        # Show weak topics and generate button if we have them
        if hasattr(st.session_state, 'practice_weak_topics') and st.session_state.practice_weak_topics:
            weak = st.session_state.practice_weak_topics
            st.info(f"📌 Weak topics: **{', '.join(weak)}**")

            if st.button("Generate Practice Questions"):
                with st.spinner("🤖 Generating fresh questions with AI..."):
                    quiz_questions = []
                    for topic in weak:
                        for _ in range(2):  # 2 questions per topic
                            try:
                                new_q = generate_question(topic)
                                quiz_questions.append(new_q)
                            except Exception as e:
                                st.warning(f"Failed to generate question for {topic}: {e}")

                    if quiz_questions:
                        random.shuffle(quiz_questions)
                        st.session_state.practice_questions = quiz_questions
                        st.session_state.practice_started = True
                        st.session_state.practice_current = 0
                        st.session_state.practice_score = 0
                        st.session_state.practice_answers = []
                        st.rerun()
                    else:
                        st.error("Could not generate any questions. Check API connection.")

    # Run the practice quiz
    elif st.session_state.practice_current < len(st.session_state.practice_questions):
        questions_list = st.session_state.practice_questions
        idx = st.session_state.practice_current
        q = questions_list[idx]
        total = len(questions_list)

        st.progress((idx + 1) / total)
        st.subheader(f"Question {idx + 1} of {total} ({q['topic']})")
        st.write(f"**{q['question']}**")

        options = [f"{letter}. {text}" for letter, text in q["options"].items()]
        choice = st.radio("Choose your answer:", options, key=f"pq{idx}")

        if st.button("Submit Answer", key=f"submit_pq{idx}"):
            selected_letter = choice[0]
            is_correct = selected_letter == q["answer"]

            # Save to database
            save_result(
                st.session_state.practice_name,
                q["topic"],
                q["question"],
                is_correct,
            )

            if is_correct:
                st.success("✅ Correct!")
                st.session_state.practice_score += 1
            else:
                st.error(f"❌ Incorrect. The answer was {q['answer']}.")

            st.session_state.practice_answers.append({
                "question": q["question"],
                "topic": q["topic"],
                "selected": selected_letter,
                "correct": q["answer"],
                "is_correct": is_correct,
            })

            st.session_state.practice_current += 1
            if st.session_state.practice_current < total:
                if st.button("Next Question →"):
                    st.rerun()
            else:
                st.rerun()

    # Practice quiz results
    else:
        score = st.session_state.practice_score
        total = len(st.session_state.practice_questions)
        pct = (score / total) * 100 if total > 0 else 0

        st.balloons()
        st.subheader("🎉 Practice Quiz Complete!")
        st.metric("Score", f"{score}/{total} ({pct:.0f}%)")

        if pct == 100:
            st.success("Perfect! You've mastered your weak topics! 🌟")
        elif pct >= 80:
            st.success("Great improvement! Keep it up! 🌟")
        elif pct >= 60:
            st.info("Good progress! Practice more to improve.")
        else:
            st.warning("Keep practicing — you'll get there!")

        st.write("---")
        st.subheader("Your Answers")
        for ans in st.session_state.practice_answers:
            icon = "✅" if ans["is_correct"] else "❌"
            st.write(f"{icon} **{ans['topic']}** — {ans['question'][:60]}...")

        if st.button("Practice Again"):
            st.session_state.practice_started = False
            st.session_state.practice_questions = []
            st.session_state.practice_current = 0
            st.session_state.practice_score = 0
            st.session_state.practice_answers = []
            st.rerun()
