import sqlite3
import hashlib
import random
import re
import time
from getpass import getpass


DB_NAME = "bank.db"
ran_time = random.randint(1, 5)

def start_up():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL CHECK(full_name <> ''),
                username TEXT NOT NULL UNIQUE CHECK(username <> ''),
                password TEXT NOT NULL CHECK(password <> ''),
                balance INT NOT NULL CHECK(balance <> ''),
                account_number TEXT NOT NULL UNIQUE CHECK(account_number <> '')
            );
                       
""")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,          
            amount REAL NOT NULL,
            counterparty_name TEXT,      
            counterparty_account TEXT,   
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        
def collect_input_and_validate(field_name):
    while True:
        value = input(f"Enter your {field_name}: ").strip()

        if not value:
            print(f"{field_name} is required.")
            continue
        return value



def generate_account_number(cursor):
    while True:
        account_number = str(random.randint(10000000, 99999999))

        cursor.execute(
            "SELECT 1 FROM users WHERE account_number = ?",
            (account_number,)
        )

        if cursor.fetchone() is None:
            return account_number

def validate_full_name():
    while True:
        first_name = collect_input_and_validate("First name").strip()
        last_name = collect_input_and_validate("Last name").strip()
        full_name = first_name + " " + last_name

        if not full_name:
            print("Full name cannot be empty.")
            continue

        if len(full_name) < 4:
            print("Full name must be at least 4 characters.")
            continue

        if len(full_name) > 255:
            print("Full name cannot exceed 255 characters.")
            continue

        if not re.fullmatch(r"[A-Za-z ]+", full_name):
            print("Full name must contain only letters and spaces.")
            continue

        return full_name



def validate_username(cursor):

    while True:

        username = collect_input_and_validate("username")

        if not username:
            print("Username cannot be empty.")
            continue

        if len(username) < 3 or len(username) > 20:
            print("Username must be between 3 and 20 characters.")
            continue

        # Only letters, numbers, underscores
        if not re.fullmatch(r"\w+", username):
            print("Username can only contain letters, numbers and underscores.")
            continue

        cursor.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,)
        )

        if cursor.fetchone():
            print("Username already exists.")
            continue

        return username


def validate_password():

    while True:

        password = getpass("Enter password: ").strip()

        if len(password) < 8 or len(password) > 30:
            print("Password must be between 8 and 30 characters.")
            continue

        if not re.search(r"[A-Z]", password):
            print("Password must contain at least one uppercase letter.")
            continue

        if not re.search(r"[a-z]", password):
            print("Password must contain at least one lowercase letter.")
            continue

        if not re.search(r"\d", password):
            print("Password must contain at least one number.")
            continue

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            print("Password must contain at least one special character.")
            continue

        confirm_password = getpass("Confirm password: ").strip()

        if password != confirm_password:
            print("Passwords do not match.")
            continue

        return password



def validate_deposit():

    while True:

        deposit = collect_input_and_validate("initial deposit(not less than 2000)")

        try:
            deposit = int(deposit)

            if deposit < 0:
                print("Deposit cannot be negative.")
                continue

            if deposit < 2000:
                print("Minimum opening balance is 2000 naira.")
                continue

            return deposit

        except ValueError:
            print("Deposit must be a numeric value.")
            continue



def sign_up():

    print("\n========== SIGN UP ==========\n")

    with sqlite3.connect(DB_NAME) as conn:

        cursor = conn.cursor()

        full_name = validate_full_name()
        username = validate_username(cursor)
        password = validate_password()
        balance = validate_deposit()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        account_number = generate_account_number(cursor)

        try:

            cursor.execute("""
            INSERT INTO users
            (full_name, username, password, balance, account_number)
            VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                username,
                hashed_password,
                balance,
                account_number
            ))

            conn.commit()

            print("Account created successfully.")
            print(f"Your account number is {account_number}")

        except sqlite3.IntegrityError as e:

            if "username" in str(e):
                print("Username is already taken")

            elif "account_number" in str(e):
                print("Account number already exists")

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
            print('\nLoading...🔃')
            time.sleep(ran_time)
            print("\nLogin Successful ✅ \n")
            dashboard(user_id, username)
        else:
            print("Invalid credentials ❌")
            start_up()

        
    
def deposit(user_id):
        
    print("\n**************************DEPOSIT**************************\n")

        
    while True:
        try:
            amount = int(input('Enter amount to be deposited: '))
        except ValueError as e:
            print(f"Please enter a valid amount {e}\n")
            continue
        else:
            if amount < 100:
                print('Deposit amount cannot be less than ₦100\n')
                continue
            break
        
            
           
                
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor() 
        user_balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
            
        current_balance = user_balance[0]
        new_balance = current_balance + amount

        cursor.execute("""UPDATE users
                            SET balance = ?
                            WHERE id = ?""", (new_balance, user_id))
        
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)",(user_id, "deposit", amount, "NULL", "NULL"))

    print('\nLoading...🔃')
    time.sleep(ran_time)

    print("\nDeposit Successful ✅ \n")

    input("Press Enter to return to dashboard...\n")    
    return

def withdraw(user_id):

    print("\n************ WITHDRAW ************\n")

    while True:
        try:
            amount = int(input("Enter amount to withdraw: "))
        except ValueError as e:
            print(f"Please enter a valid amount {e}\n")
            continue

        if amount < 100:
            print("Minimum withdrawal is ₦100\n")
            continue
        break


    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT balance FROM users WHERE id=?", (user_id,)).fetchone()
        balance = user[0]

        if amount > balance:
            print("Insufficient funds ❌")
            return

        new_balance = balance - amount

        cursor.execute(
            "UPDATE users SET balance=? WHERE id=?",
            (new_balance, user_id)
        )

        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)",(user_id, "withdraw", amount, "NULL", "NULL"))


    print('\nLoading...🔃')
    time.sleep(ran_time)

    print("Withdrawal successful ✅")

    input("\nPress Enter to return to dashboard...\n")

    return

def balance(user_id):
    
    print("\n**************************BALANCE**************************\n")
    
    while True:

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            user_balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user_balance :
                print('Invalid ❌ \n')
                continue
            else:
                current_balance = user_balance[0]
                break


    print("\nLoading...🔃\n")
    time.sleep(ran_time)

    print(f"Your balance is ₦{current_balance:,.2f}\n")

    input("Press Enter to return to dashboard...\n")
    return
            

def transfer(user_id):

    print("\n************ TRANSFER ************\n")

    account = input('Enter beneficiary account number: ').strip()
    while True:
        try:
            amount = int(input("Enter amount to Transfer: "))
        except ValueError as e:
            print(f"Please enter a valid amount {e}\n")
            continue

        if amount < 100:
            print("Minimum withdrawal is ₦100\n")
            continue
        break


    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT full_name, balance, account_number FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        receiver = cursor.execute("SELECT id, full_name, balance FROM users WHERE account_number = ?",(account,)).fetchone()

        if not user:
            print("\nInvalid pin ❌\n")
            return
        
        if account == user[2]:
            print('\nYou can not transfer to yourself ❌\n')
            return
        
        
        
        if not receiver:
            print("\nAccount does not exist ❌\n")
            return

        senders_name = user[0]
        senders_acc_number = user[2]
        
        receivers_id = receiver[0]
        receivers_name = receiver[1]
        
        balance = user[1]
        receiver_balance = receiver[2]

        if amount > balance:
            print("\nInsufficient funds ❌\n")
            return

        new_balance = balance - amount
        receiver_new_bal = receiver_balance + amount

        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_number = ?",
            (receiver_new_bal,account)
        )

        cursor.execute(
            "UPDATE users SET balance = ? WHERE id = ?",
            (new_balance,user_id)
        )

        cursor.execute(
            "INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)",
            (user_id, "Transfer", amount, receivers_name, account)
        )

        cursor.execute(
            "INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)",
            (receivers_id, "Transfer recieved", amount, senders_name, senders_acc_number)
        )
    print('\nLoading...🔃')
    time.sleep(ran_time)

    print("\nTransfer successful ✅")

    input("Press Enter to return to dashboard...\n")

    return
 
def account_details(user_id):

    print("\n************ ACCOUNT DETAILS ************\n")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        user_details =  cursor.execute("SELECT full_name, username, account_number FROM users WHERE id = ?", (user_id,)).fetchone()
        fullname = user_details[0]
        username = user_details[1]
        account_number = user_details[2]
    
    print("\nLoading...🔃\n")
    time.sleep(ran_time)

    print(f'Fullname: {fullname}')
    print(f'Username: {username}')
    print(f'Account_number: {account_number}\n')

    input("Press Enter to return to dashboard...\n")
    return   
   
def transaction_history(user_id):

    print("\n************************** Transaction History **************************\n")
    print('\nLoading...🔃')
    time.sleep(ran_time)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        transactions = cursor.execute(
            "SELECT type, amount, counterparty_name, counterparty_account ,timestamp FROM transactions WHERE user_id = ?",
            (user_id,)
        ).fetchall()

        if not transactions:
            print("No transactions yet.\n")
            input("Press Enter to return to dashboard...\n")
            return
        

        print(f"{'No':<4}{'Type':<18}{'Amount':<12}{'Counterparty':<22}{'Account':<12}{'Date'}")
        print("-" * 88)


        for i, t in enumerate(transactions, start=1):

            t_type = t[0]
            amount = f"₦{t[1]:,.2f}"
            name = t[2] if t[2] != "NULL" else "-"
            account = t[3] if t[3] != "NULL" else "-"
            timestamp = t[4]
            print(f"{i:<4}{t_type:<18}{amount:<12}{name:<22}{account:<12}{timestamp}")
        print("-" * 88)

    

    input("Press Enter to return to dashboard...\n")

    return

        
def dashboard(user_id, username):
    menu = """
    Would you like to: 
1. Make a deposit.
2. Make a withdrawal.
3. View your balance.
4. View your transaction history.
5. Make a transfer.
6. View your account deatils.
7. Quit.
"""

    while True:
        print("**************************DASHBOARD**************************")

        print(f"Welcome to your dashboard, {username} 👋")
        print(menu)

        choice = input('Enter the operation your want to carry out: ').strip()

        if choice == '1':
            deposit(user_id)
        elif choice == '2':
            withdraw(user_id)
        elif choice == '3':
            balance(user_id)
        elif choice == '4':
            transaction_history(user_id)
        elif choice == '5':
            transfer(user_id)
        elif choice == '6':
            account_details(user_id)
        elif choice == '7':
            print('Logging out.....')
            time.sleep(ran_time)
            return
        else:
            print('\n Invalid operation entered \n')
            continue

start_up()


menu = """
        1. Sign Up
        2. Log In
        3. Quit
    """

while True:
    print()
    print("**************************HOME**************************")
    print(menu)
    choice = input("Choose an option from the menu above: ").strip()

    if choice == "1":
        sign_up()
    elif choice == "2":
        log_in()
    elif choice == "3":
        print("Thanks for banking with us👋...")
        break
    else:
        print()
        print("Invalid choice. Please select from option 1-3.")
        




# password_winnie = 54</?zjXSj2?