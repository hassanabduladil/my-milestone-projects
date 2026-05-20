print(int(""))
def dashboard(user_id, username):
    print("**************************DASHBOARD**************************")

    print(f"Welcome to your dashboard, {username} 👋")
    menu = """
    Would you like to: 
1. Make a deposit.
2. Make a withdrawal.
3. View your balance.
4. View your transaction history.
5. Make a transfer
6. View your account deatils.
"""

def sign_up():

    print("**************************SIGN UP**************************")

    first_name = collect_input_and_validate("First name")
    last_name = collect_input_and_validate("Last name")
    username = collect_input_and_validate("Username")

    full_name = first_name + " " + last_name

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

    while True:
        try:
            balance = int(collect_input_and_validate("Initial deposit"))

            if balance < 2000:
                print("Minimum deposit is 2000")
                continue

           
        except ValueError:
            print("Invalid. Please enter a deposit amount.")
            continue 
        break

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

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

    print("Signed up Successfully")
    log_in()
