questions_and_answers = [
{"question": """What is 2 + 2?
a) 3
b) 4
c) 5
d) 6
"""
, "answer": "b"}, 
{"question": """What color is the sky on a clear day?
a) Red
b) Blue
c) Green
d) Yellow""", "answer": "b"},
{"question": """How many legs does a spider have?
a) 6
b) 7
c) 8
d) 9""", "answer": "c"},
{"question": 
"""What sound does a cow make?
a) Meow
b) Bark
c) Moo
d) Quack""", "answer": "c"},
{"question": """What is the opposite of 'hot'?
a) Warm
b) Cold
c) Cool
d) Boiling""", "answer": "b"}
]
score = 0

for question_and_answer in questions_and_answers:
    # each_question, each_answer = question_and_answer.items()
    print(question_and_answer["question"])
    option = input("Enter an option from a to d: ")
    print()
    if option == question_and_answer["answer"]:
        score += 1
    if option not in ["a", "b", "c", "d"]:
        print("Invalid option")
        continue

print(f"At the end of the CBT exam, you scored {score} points")