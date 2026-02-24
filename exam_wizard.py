# Project Overview:
# Develop an Exam Wizard program in Python that hardcodes a set of at least 5 theory 
# questions and evaluates the student's answers based on the presence of specific keywords or phrases. The program should ask these questions to the user one by one and display the user's score at the end.

# Requirements:
# Hardcode Questions and Keywords:
# Create at least 5 theory questions.
# For each question, determine the essential keywords or phrases that should be included in the ideal answer.
# Assign weights to each keyword based on its importance.
# Question Prompting:
# Prompt the user with each question one by one.
# Allow the user to input their answer for each question.
# Scoring System:
# Evaluate the user's answers based on the presence of the specified keywords..
# Keep track of the user's score.
# Display Results:
# At the end of the quiz, display the user's total score out of the max score e.g. 10/12.



questions_and_keywords = [
    {"question": "Explain the process of photosynthesis.? ", "keywords": {"photosynthesis": 2, "light": 1, "chemical": 0.5, "energy": 0.5, "chloroplasts": 2, "chlorophyll": 1, "carbon": 0.5, "dioxide": 0.5, "water": 1, "glucose": 1, "oxygen": 1, "atp": 1}},
    {"question": "Explain the water cycle.? ", "keywords": {"evaporation": 2, "condensation": 2, "precipitation": 1, "sun": 2, "clouds": 1, "collection": 1, "water": 1}},
    {"question": "Explain the law of demand? ", "keywords": {"price": 2, "quantity": 0.5, "demanded": 0.5, "opposite": 1, "ceteris": 1, "paribus": 2}},
    {"question": "Explain the difference between a list and a tuple in python? ", "keywords": {"list": 2, "tuple": 2, "mutable": 1, "immutable": 1}},
    {"question": "What is a variable in python.? ", "keywords": {"store": 2, "data": 1, "value": 1, "memory": 2}}
    ]

score = 0
for question_and_keyword in questions_and_keywords:
    print(question_and_keyword["question"])
    user_answer = input("Enter your answer: ").lower().split()

    for each_keywords, weight in question_and_keyword["keywords"].items():
        if each_keywords in user_answer:
            score += weight

print(f"{score} out of 34 points")
