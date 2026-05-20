import sqlite3
import hashlib

from getpass import getpass

DB_NAME = "facebook.db"

def start_up():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL CHECK(first_name <> ''),
                last_name TEXT NOT NULL CHECK(last_name <> ''),
                username TEXT NOT NULL UNIQUE CHECK(username <> ''),
                password TEXT NOT NULL CHECK(password <> '')
            );
                       
""")


def collect_input_and_validate(field_name):
    while True:
        value = input(f"Enter your {field_name}: ").strip()

        if not value:
            print(f"{field_name} is required.")
            continue
        return value



def sign_up():

    print("**************************SIGN UP**************************")


    first_name = collect_input_and_validate("First name")
    last_name = collect_input_and_validate("Last name")
    username = collect_input_and_validate("Username")

    while True:
        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password is required.")
            continue

        confirm_password = getpass("Confirm your password: ").strip()
        if password != confirm_password:
            print("Passwords don't match.")
            continue
        break


    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        try:
            cursor.execute("INSERT INTO users (first_name, last_name, username, password) VALUES (?, ?, ?, ?)", (first_name, last_name, username, hashed_password))
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                print("Username is already taken")
            else:
                print("A user with those details already exists")
            return

    print("Signed up Successfully")
    log_in()


def log_in():
    print("**************************LOG IN**************************")
    username = collect_input_and_validate("Username")

    while True:
        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password is required.")
            continue
        break

    hashed_password = hashlib.sha256(password.encode()).hexdigest()



    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        user = cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password)).fetchone()

        if user is not None:
            user_id = user[0]
            print("Login Successful")
            dashboard(user_id, username)
        else:
            print("Invalid credentials")
    

def dashboard(user_id, username):
    print("**************************DASHBOARD**************************")

    print(f"Welcome to your dashboard, {username} 👋")
    menu = """
1. Make a Post
2. View Your Profile
3. View your timeline
4. Quit
"""

    while True:
        print(menu)
        choice = input("Choose an option from the menu above: ").strip()

        if choice == "1":
            print("Post Created")
        elif choice == "2":
            print("Profile Viewed")
        elif choice == "3":
            print("Timeline Viewed")
        elif choice == "4":
            print("Going back to main menu...")
            break
        else:
            print("Invalid choice")



start_up()

menu = """
1. Sign Up
2. Log In
3. Quit
"""

while True:
    print(menu)

    choice = input("Choose an option from the menu above: ").strip()

    if choice == "1":
        sign_up()
    elif choice == "2":
        log_in()
    elif choice == "3":
        print("Quitting facebook....")
        break
    else:
        print("Invalid choice")