"""quiz.py — A simple multiple-choice quiz for Data Science beginners."""

# Each question is a dictionary with: question, options (A-D), and the correct answer
questions = [
    {
        "question": "What is the correct way to create a list in Python?",
        "options": {
            "A": "list = (1, 2, 3)",
            "B": "list = [1, 2, 3]",
            "C": "list = {1, 2, 3}",
            "D": "list = <1, 2, 3>",
        },
        "answer": "B",
    },
    {
        "question": "Which library is most commonly used for numerical computing in Python?",
        "options": {
            "A": "pandas",
            "B": "matplotlib",
            "C": "numpy",
            "D": "seaborn",
        },
        "answer": "C",
    },
    {
        "question": "What does the len() function do?",
        "options": {
            "A": "Returns the length of a list, string, or other collection",
            "B": "Converts a number to a string",
            "C": "Rounds a number to the nearest integer",
            "D": "Opens a file for reading",
        },
        "answer": "A",
    },
    {
        "question": "What is the correct syntax to define a function in Python?",
        "options": {
            "A": "function my_func():",
            "B": "def my_func():",
            "C": "define my_func():",
            "D": "func my_func():",
        },
        "answer": "B",
    },
    {
        "question": "What data type is the value True in Python?",
        "options": {
            "A": "int",
            "B": "str",
            "C": "bool",
            "D": "float",
        },
        "answer": "C",
    },
]


def run_quiz():
    """Run the quiz: ask questions, check answers, show the final score."""
    score = 0
    total = len(questions)

    print("=" * 50)
    print("       DATA SCIENCE BASICS — PYTHON QUIZ")
    print("=" * 50)
    print(f"\nThere are {total} questions. Type A, B, C, or D to answer.\n")

    for i, q in enumerate(questions, start=1):
        print(f"Question {i}: {q['question']}")
        for letter, text in q["options"].items():
            print(f"   {letter}. {text}")

        while True:
            user_answer = input("\nYour answer (A/B/C/D): ").strip().upper()
            if user_answer in ("A", "B", "C", "D"):
                break
            print("Invalid input. Please type A, B, C, or D.")

        if user_answer == q["answer"]:
            print("   ✅ Correct!\n")
            score += 1
        else:
            print(f"   ❌ Incorrect. The answer was {q['answer']}.\n")

    print("=" * 50)
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
    print("=" * 50)


if __name__ == "__main__":
    run_quiz()
