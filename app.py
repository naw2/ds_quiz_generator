"""app.py — Streamlit web UI for the Personalized Quiz Generator.

Run with:  streamlit run app.py

Pages:
  1. Home          — welcome + overview
  2. Take Quiz     — 10 dynamic questions with difficulty selection
  3. My Progress   — topic-by-topic accuracy with charts
  4. Practice Quiz — AI-generated questions for weak topics

Style: Duolingo-inspired with timers, feedback cards, and explanations.
"""

import streamlit as st
import random
import time
import streamlit.components.v1 as components

# Import helpers from our existing scripts
from database import setup_database, save_result, DB_FILE
from analyze import get_topic_breakdown, WEAK_THRESHOLD
from generate_question import generate_question
from quiz import generate_quiz_questions, TOPICS, DIFFICULTY_LEVELS

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Quiz Generator",
    page_icon="🎯",
    layout="centered",
)

# ---------------------------------------------------------
# NAME ENTRY — runs on every page load
# ---------------------------------------------------------
# Ask the user for their name before showing the quiz
if "student_name" not in st.session_state or not st.session_state.student_name:
    # Show welcome page
    st.title("🎯 Personalized Quiz Generator")
    st.write("")
    st.write("### Welcome! Please enter your name to continue.")
    st.write("Type your name below to take quizzes, track your progress, and practice.")
    st.write("")

    with st.form("name_form"):
        name_input = st.text_input("Your name", placeholder="e.g. Khin")
        submitted = st.form_submit_button("Start Quiz →", use_container_width=True)

        if submitted and name_input.strip():
            st.session_state.student_name = name_input.strip()
            st.rerun()
        elif submitted:
            st.error("Please enter your name to continue.")

    st.stop()  # Stop here — don't show anything else until name is entered

# ---------------------------------------------------------
# CUSTOM CSS — Duolingo-inspired styling
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Green progress bar like Duolingo */
    .stProgress > div > div > div > div {
        background-color: #58cc02 !important;
    }

    /* Feedback cards */
    .feedback-correct {
        background-color: #d7ffb8;
        border: 2px solid #58cc02;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
    }
    .feedback-wrong {
        background-color: #ffdfe0;
        border: 2px solid #ff4b4b;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
    }
    .feedback-timeout {
        background-color: #fff3cd;
        border: 2px solid #ff9f43;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
    }

    /* Timer display */
    .timer-display {
        font-size: 1.4em;
        font-weight: bold;
        text-align: center;
        padding: 8px 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    .timer-normal { color: #58cc02; background-color: #e8f5e9; }
    .timer-warning { color: #ff9f43; background-color: #fff3cd; }
    .timer-critical { color: #ff4b4b; background-color: #ffdfe0; }

    /* Score display */
    .score-badge {
        background: linear-gradient(135deg, #58cc02, #46a302);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 4px;
    }

    /* Explanation box */
    .explanation-box {
        background-color: #f0f4ff;
        border-left: 4px solid #1cb0f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 10px 0;
    }

    /* Topic tag */
    .topic-tag {
        background-color: #e8e8e8;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        display: inline-block;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPER: COUNTDOWN TIMER COMPONENT
# ---------------------------------------------------------
def show_timer(seconds_left, total_seconds=20):
    """Display a countdown timer using embedded JavaScript."""
    if seconds_left > 10:
        timer_class = "timer-normal"
    elif seconds_left > 5:
        timer_class = "timer-warning"
    else:
        timer_class = "timer-critical"

    st.markdown(
        f'<div class="timer-display {timer_class}">⏱️ {int(seconds_left)}s</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# HELPER: ENCOURAGING MESSAGES
# ---------------------------------------------------------
CORRECT_MESSAGES = [
    "Great job! 🎉",
    "You're on fire! 🔥",
    "Awesome! ⭐",
    "Nailed it! 💪",
    "Keep it up! 🚀",
    "Brilliant! 🌟",
    "Perfect! ✨",
    "Well done! 🏆",
]

WRONG_MESSAGES = [
    "Not quite — but you'll get it! 💪",
    "Good try! Keep going! 🌱",
    "Almost there! 🎯",
    "Don't worry, learning takes time! 📚",
    "You'll get it next time! 🔄",
    "Keep practicing! 💡",
]


def random_correct_msg():
    return random.choice(CORRECT_MESSAGES)


def random_wrong_msg():
    return random.choice(WRONG_MESSAGES)


# ---------------------------------------------------------
# HELPER: SHOW FEEDBACK AFTER ANSWERING
# ---------------------------------------------------------
def show_feedback(is_correct, correct_answer, explanation, time_up=False):
    """Display Duolingo-style feedback card after an answer."""
    if time_up:
        st.markdown("""
        <div class="feedback-timeout">
            <strong style="font-size:1.3em;">⏰ Time's up!</strong><br>
            <span>The correct answer was <strong>{}</strong></span>
        </div>
        """.format(correct_answer), unsafe_allow_html=True)
        st.info(random_wrong_msg())
    elif is_correct:
        st.markdown("""
        <div class="feedback-correct">
            <strong style="font-size:1.3em;">✅ Correct!</strong>
        </div>
        """, unsafe_allow_html=True)
        st.success(random_correct_msg())
    else:
        st.markdown("""
        <div class="feedback-wrong">
            <strong style="font-size:1.3em;">❌ Incorrect</strong><br>
            <span>The correct answer was <strong>{}</strong></span>
        </div>
        """.format(correct_answer), unsafe_allow_html=True)
        st.warning(random_wrong_msg())

    # Show explanation (for wrong answers and timeouts)
    if explanation and (not is_correct or time_up):
        st.markdown(f"""
        <div class="explanation-box">
            💡 <strong>Explanation:</strong> {explanation}
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# HELPER: SHOW A QUIZ QUESTION (used by both quiz pages)
# ---------------------------------------------------------
def show_question(q, q_num, total, key_prefix="q"):
    """Display one quiz question with options. Returns the selected answer letter or None."""
    # Topic and difficulty tags
    diff_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(
        q.get("difficulty", "beginner"), "🟢"
    )
    st.markdown(
        f'<span class="topic-tag">📖 {q["topic"]}</span>'
        f'<span class="topic-tag">{diff_emoji} {q.get("difficulty", "beginner")}</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.subheader(f"Question {q_num} of {total}")
    st.write(f"**{q['question']}**")

    # Radio buttons for options
    options = [f"{letter}. {text}" for letter, text in q["options"].items()]
    choice = st.radio("Choose your answer:", options, key=f"{key_prefix}{q_num}")
    selected_letter = choice[0]  # "A", "B", "C", or "D"
    return selected_letter


# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("🎯 Quiz Generator")
st.sidebar.write(f"👋 **{st.session_state.student_name}**")
if st.sidebar.button("Change Name"):
    st.session_state.student_name = ""
    st.rerun()
st.sidebar.write("---")
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
    1. **Take a quiz** — choose your difficulty level and answer 10 AI-generated questions
    2. **See your progress** — find out which topics you're weak in
    3. **Practice** — get fresh AI-generated questions targeting your weak spots

    ### Difficulty levels
    - 🟢 **Beginner** — basic syntax, definitions, simple concepts
    - 🟡 **Intermediate** — applying concepts, reading code, combining features
    - 🔴 **Advanced** — edge cases, tricky behavior, performance trade-offs

    ### Topics covered
    - Lists
    - NumPy
    - Built-in functions
    - Functions
    - Data types

    ### ✨ New features
    - ⏱️ **20-second timer** per question — think fast!
    - 💡 **Explanations** when you get it wrong — learn from mistakes
    - 🎯 **Instant feedback** — see if you're right before moving on

    👈 **Use the sidebar to get started!**
    """)

# ---------------------------------------------------------
# PAGE: TAKE QUIZ
# ---------------------------------------------------------
elif page == "Take Quiz":
    st.title("📝 Take the Quiz")

    # Initialize session state (student_name comes from name entry above)
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.quiz_difficulty = "beginner"
        st.session_state.quiz_questions = []
        st.session_state.answers = []
        st.session_state.quiz_feedback = False       # True = showing feedback
        st.session_state.quiz_time_up = False         # True = timer expired
        st.session_state.quiz_start_time = 0          # when current question appeared

    TIMER_SECONDS = 20  # seconds per question

    # Step 1: Choose difficulty (name comes from name entry)
    if not st.session_state.quiz_started:
        st.write(f"Logged in as: **{st.session_state.student_name}**")

        difficulty = st.radio(
            "Choose your difficulty level:",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {
                "beginner": "🟢 Beginner — basic syntax and definitions",
                "intermediate": "🟡 Intermediate — applying concepts, reading code",
                "advanced": "🔴 Advanced — edge cases, tricky behavior",
            }[x],
        )

        if st.button("Start Quiz"):
            st.session_state.quiz_difficulty = difficulty
            setup_database()

            # Generate questions via API
            with st.spinner(f"🤖 Generating 10 {difficulty} questions... This may take a moment."):
                questions = generate_quiz_questions(difficulty)

            if questions:
                st.session_state.quiz_questions = questions
                st.session_state.quiz_started = True
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.answers = []
                st.session_state.quiz_feedback = False
                st.session_state.quiz_time_up = False
                st.session_state.quiz_start_time = time.time()
                st.rerun()
            else:
                st.error("❌ Could not generate questions. Check your API connection and try again.")

    # Step 2: Show questions one at a time
    elif st.session_state.current_q < len(st.session_state.quiz_questions):
        questions = st.session_state.quiz_questions
        q = questions[st.session_state.current_q]
        q_num = st.session_state.current_q + 1
        total = len(questions)

        # Progress bar and score header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(q_num / total)
        with col2:
            st.markdown(
                f'<div class="score-badge">⭐ {st.session_state.score}/{q_num - 1}</div>',
                unsafe_allow_html=True,
            )

        # Check if we're in FEEDBACK mode (after answering)
        if st.session_state.quiz_feedback:
            # Show the question again (read-only context)
            st.subheader(f"Question {q_num} of {total}")
            st.caption(f"Topic: {q['topic']} | Difficulty: {q.get('difficulty', 'beginner')}")
            st.write(f"**{q['question']}**")

            # Show feedback
            last = st.session_state.answers[-1]
            show_feedback(
                last["is_correct"],
                last["correct"],
                q.get("explanation", ""),
                time_up=st.session_state.quiz_time_up,
            )

            # Continue button
            if st.button("Continue ➡️", key=f"continue_{q_num}"):
                st.session_state.current_q += 1
                st.session_state.quiz_feedback = False
                st.session_state.quiz_time_up = False
                st.session_state.quiz_start_time = time.time()
                st.rerun()

        # ANSWERING mode — show question and options
        else:
            # Timer
            elapsed = time.time() - st.session_state.quiz_start_time
            remaining = max(0, TIMER_SECONDS - elapsed)
            show_timer(remaining, TIMER_SECONDS)

            # Auto-expire if time ran out
            if remaining <= 0:
                # Time's up — mark as wrong
                is_correct = False
                save_result(
                    st.session_state.student_name,
                    q["topic"],
                    q["question"],
                    is_correct,
                    st.session_state.quiz_difficulty,
                )
                st.session_state.answers.append({
                    "question": q["question"],
                    "topic": q["topic"],
                    "selected": None,
                    "correct": q["answer"],
                    "is_correct": is_correct,
                })
                st.session_state.quiz_feedback = True
                st.session_state.quiz_time_up = True
                st.rerun()

            # Show the question
            selected_letter = show_question(q, q_num, total, key_prefix="tq")

            # Check button (Duolingo uses "Check", not "Submit")
            if st.button("Check ✅", key=f"check_{q_num}"):
                is_correct = selected_letter == q["answer"]

                # Save to database
                save_result(
                    st.session_state.student_name,
                    q["topic"],
                    q["question"],
                    is_correct,
                    st.session_state.quiz_difficulty,
                )

                if is_correct:
                    st.session_state.score += 1

                st.session_state.answers.append({
                    "question": q["question"],
                    "topic": q["topic"],
                    "selected": selected_letter,
                    "correct": q["answer"],
                    "is_correct": is_correct,
                })

                st.session_state.quiz_feedback = True
                st.session_state.quiz_time_up = False
                st.rerun()

    # Step 3: Show final results
    else:
        score = st.session_state.score
        total = len(st.session_state.quiz_questions)
        pct = (score / total) * 100

        st.balloons()
        st.subheader("🎉 Quiz Complete!")
        st.metric("Score", f"{score}/{total} ({pct:.0f}%)")

        if pct == 100:
            st.success("Perfect score! You're a Python master! 🌟")
        elif pct >= 80:
            st.success("Great job! Almost perfect! 🌟")
        elif pct >= 60:
            st.info("Good effort! Keep practicing to improve. 💪")
        else:
            st.warning("Keep studying — you'll get it! 📚")

        # Show detailed breakdown
        st.write("---")
        st.subheader("Your Answers")
        for ans in st.session_state.answers:
            icon = "✅" if ans["is_correct"] else "❌"
            selected = ans["selected"] if ans["selected"] else "⏰"
            st.write(f"{icon} **{ans['topic']}** — {ans['question'][:60]}... → You answered: {selected}")

        if st.button("Take Quiz Again"):
            st.session_state.quiz_started = False
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.quiz_questions = []
            st.session_state.answers = []
            st.session_state.quiz_feedback = False
            st.session_state.quiz_time_up = False
            st.rerun()

# ---------------------------------------------------------
# PAGE: MY PROGRESS
# ---------------------------------------------------------
elif page == "My Progress":
    st.title("📊 My Progress")

    st.write(f"Showing progress for: **{st.session_state.student_name}**")
    setup_database()
    breakdown = get_topic_breakdown(st.session_state.student_name)

    if not breakdown:
        st.warning(f"No quiz history found for '{st.session_state.student_name}'.")
        st.write("Take the quiz first!")
    else:
        # Build a table
        st.subheader(f"Topic Report for {st.session_state.student_name}")

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
        st.session_state.practice_name = st.session_state.student_name
        st.session_state.practice_difficulty = "beginner"
        st.session_state.practice_answers = []
        st.session_state.practice_feedback = False
        st.session_state.practice_time_up = False
        st.session_state.practice_start_time = 0

    TIMER_SECONDS = 20  # seconds per question

    if not st.session_state.practice_started:
        st.write(f"Logged in as: **{st.session_state.student_name}**")

        # Difficulty selector for practice too
        practice_difficulty = st.radio(
            "Practice difficulty level:",
            ["beginner", "intermediate", "advanced"],
            format_func=lambda x: {
                "beginner": "🟢 Beginner",
                "intermediate": "🟡 Intermediate",
                "advanced": "🔴 Advanced",
            }[x],
            key="practice_diff",
        )

        if st.button("Find My Weak Topics"):
            setup_database()
            from practice_quiz import find_weak_topics
            weak = find_weak_topics(st.session_state.student_name)

            if weak is None:
                st.warning(f"No quiz history for '{st.session_state.student_name}'. Take the main quiz first!")
            elif not weak:
                st.success("🎉 No weak topics! You're doing great!")
            else:
                st.session_state.practice_name = st.session_state.student_name
                st.session_state.practice_difficulty = practice_difficulty
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
                                new_q = generate_question(topic, difficulty=practice_difficulty)
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
                        st.session_state.practice_feedback = False
                        st.session_state.practice_time_up = False
                        st.session_state.practice_start_time = time.time()
                        st.rerun()
                    else:
                        st.error("Could not generate any questions. Check API connection.")

    # Run the practice quiz
    elif st.session_state.practice_current < len(st.session_state.practice_questions):
        questions_list = st.session_state.practice_questions
        idx = st.session_state.practice_current
        q = questions_list[idx]
        total = len(questions_list)

        # Progress bar and score header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress((idx + 1) / total)
        with col2:
            st.markdown(
                f'<div class="score-badge">⭐ {st.session_state.practice_score}/{idx}</div>',
                unsafe_allow_html=True,
            )

        # FEEDBACK mode
        if st.session_state.practice_feedback:
            st.subheader(f"Question {idx + 1} of {total}")
            st.caption(f"Topic: {q['topic']} | Difficulty: {q.get('difficulty', 'beginner')}")
            st.write(f"**{q['question']}**")

            last = st.session_state.practice_answers[-1]
            show_feedback(
                last["is_correct"],
                last["correct"],
                q.get("explanation", ""),
                time_up=st.session_state.practice_time_up,
            )

            if st.button("Continue ➡️", key=f"p_continue_{idx}"):
                st.session_state.practice_current += 1
                st.session_state.practice_feedback = False
                st.session_state.practice_time_up = False
                st.session_state.practice_start_time = time.time()
                st.rerun()

        # ANSWERING mode
        else:
            # Timer
            elapsed = time.time() - st.session_state.practice_start_time
            remaining = max(0, TIMER_SECONDS - elapsed)
            show_timer(remaining, TIMER_SECONDS)

            # Auto-expire if time ran out
            if remaining <= 0:
                is_correct = False
                save_result(
                    st.session_state.practice_name,
                    q["topic"],
                    q["question"],
                    is_correct,
                    st.session_state.practice_difficulty,
                )
                st.session_state.practice_answers.append({
                    "question": q["question"],
                    "topic": q["topic"],
                    "selected": None,
                    "correct": q["answer"],
                    "is_correct": is_correct,
                })
                st.session_state.practice_feedback = True
                st.session_state.practice_time_up = True
                st.rerun()

            # Show question
            selected_letter = show_question(q, idx + 1, total, key_prefix="pq")

            if st.button("Check ✅", key=f"check_pq{idx}"):
                is_correct = selected_letter == q["answer"]

                save_result(
                    st.session_state.practice_name,
                    q["topic"],
                    q["question"],
                    is_correct,
                    st.session_state.practice_difficulty,
                )

                if is_correct:
                    st.session_state.practice_score += 1

                st.session_state.practice_answers.append({
                    "question": q["question"],
                    "topic": q["topic"],
                    "selected": selected_letter,
                    "correct": q["answer"],
                    "is_correct": is_correct,
                })

                st.session_state.practice_feedback = True
                st.session_state.practice_time_up = False
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
            st.info("Good progress! Practice more to improve. 💪")
        else:
            st.warning("Keep practicing — you'll get there! 📚")

        st.write("---")
        st.subheader("Your Answers")
        for ans in st.session_state.practice_answers:
            icon = "✅" if ans["is_correct"] else "❌"
            selected = ans["selected"] if ans["selected"] else "⏰"
            st.write(f"{icon} **{ans['topic']}** — {ans['question'][:60]}... → You answered: {selected}")

        if st.button("Practice Again"):
            st.session_state.practice_started = False
            st.session_state.practice_questions = []
            st.session_state.practice_current = 0
            st.session_state.practice_score = 0
            st.session_state.practice_answers = []
            st.session_state.practice_feedback = False
            st.session_state.practice_time_up = False
            st.rerun()
