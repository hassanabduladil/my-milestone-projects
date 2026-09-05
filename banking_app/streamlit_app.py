import streamlit as st
import sqlite3
import hashlib
import random
import re
import datetime
import pandas as pd

DB_NAME = "bank.db"

def init_db():
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

def generate_account_number():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        while True:
            account_number = str(random.randint(10000000, 99999999))
            cursor.execute("SELECT 1 FROM users WHERE account_number = ?", (account_number,))
            if cursor.fetchone() is None:
                return account_number

def sign_up(full_name, username, password, deposit):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        account_number = generate_account_number()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute("""
            INSERT INTO users (full_name, username, password, balance, account_number)
            VALUES (?, ?, ?, ?, ?)
            """, (full_name, username, hashed_password, deposit, account_number))
            conn.commit()
            return True, f"Account created successfully. Your account number is {account_number}"
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username is already taken"
            elif "account_number" in str(e):
                return False, "Account number already exists"
            else:
                return False, "A user with those details already exists"

def login(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password)).fetchone()
        if user:
            return True, user[0]
        return False, "Invalid credentials"

def get_balance(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()[0]

def make_deposit(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        new_balance = balance + amount
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "deposit", amount, "NULL", "NULL"))
        conn.commit()

def make_withdrawal(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        if amount > balance:
            return False, "Insufficient funds"
        new_balance = balance - amount
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "withdraw", amount, "NULL", "NULL"))
        conn.commit()
        return True, "Withdrawal successful"

def make_transfer(user_id, amount, receiver_account):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT full_name, balance, account_number FROM users WHERE id=?", (user_id,)).fetchone()
        receiver = cursor.execute("SELECT id, full_name, balance FROM users WHERE account_number = ?", (receiver_account,)).fetchone()
        
        if not receiver:
            return False, "Account does not exist"
        if receiver_account == user[2]:
            return False, "You can not transfer to yourself"
        if amount > user[1]:
            return False, "Insufficient funds"
            
        new_balance = user[1] - amount
        receiver_new_bal = receiver[2] + amount
        
        cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (receiver_new_bal, receiver_account))
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "Transfer", amount, receiver[1], receiver_account))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (receiver[0], "Transfer received", amount, user[0], user[2]))
        
        conn.commit()
        return True, "Transfer successful"

def get_account_details(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT full_name, username, account_number FROM users WHERE id = ?", (user_id,)).fetchone()

def get_transaction_history(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT type, amount, counterparty_name, counterparty_account, timestamp FROM transactions WHERE user_id = ?", (user_id,)).fetchall()

def main():
    st.set_page_config(page_title="Banking App", layout="centered")
    init_db()

    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None

    if st.session_state.user_id is None:
        st.title("Welcome to the Banking App")
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])
        
        with tab1:
            st.header("Log In")
            with st.form("login_form"):
                log_username = st.text_input("Username")
                log_password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In")
                
                if submit_login:
                    if not log_username or not log_password:
                        st.error("Please fill in all fields")
                    else:
                        success, result = login(log_username, log_password)
                        if success:
                            st.session_state.user_id = result
                            st.session_state.username = log_username
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(result)
                            
        with tab2:
            st.header("Sign Up")
            with st.form("signup_form"):
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                reg_username = st.text_input("Username")
                reg_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                initial_deposit = st.number_input("Initial Deposit (min 2000)", min_value=0)
                submit_signup = st.form_submit_button("Sign Up")
                
                if submit_signup:
                    full_name = f"{first_name.strip()} {last_name.strip()}"
                    if not first_name or not last_name:
                        st.error("Full name cannot be empty.")
                    elif len(full_name) < 4:
                        st.error("Full name must be at least 4 characters.")
                    elif not re.fullmatch(r"[A-Za-z ]+", full_name):
                        st.error("Full name must contain only letters and spaces.")
                    elif not reg_username or len(reg_username) < 3 or len(reg_username) > 20 or not re.fullmatch(r"\w+", reg_username):
                        st.error("Username must be between 3 and 20 characters and contain only letters, numbers, and underscores.")
                    elif len(reg_password) < 8 or not re.search(r"[A-Z]", reg_password) or not re.search(r"[a-z]", reg_password) or not re.search(r"\d", reg_password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", reg_password):
                        st.error("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")
                    elif reg_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif initial_deposit < 2000:
                        st.error("Minimum opening balance is 2000 naira.")
                    else:
                        success, msg = sign_up(full_name, reg_username, reg_password, int(initial_deposit))
                        if success:
                            st.success(msg)
                            st.info("Please go to the Log In tab to log in.")
                        else:
                            st.error(msg)
    else:
        st.title(f"Dashboard - Welcome, {st.session_state.username} 👋")
        
        if st.button("Log Out"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
            
        menu = ["Make a deposit", "Make a withdrawal", "View your balance", "View transaction history", "Make a transfer", "View account details"]
        choice = st.sidebar.selectbox("Select Operation", menu)
        
        if choice == "Make a deposit":
            st.subheader("Deposit")
            with st.form("deposit_form"):
                dep_amount = st.number_input("Amount to deposit", min_value=100)
                submit_dep = st.form_submit_button("Deposit")
                if submit_dep:
                    make_deposit(st.session_state.user_id, dep_amount)
                    st.success("Deposit Successful ✅")
                    
        elif choice == "Make a withdrawal":
            st.subheader("Withdrawal")
            with st.form("withdraw_form"):
                with_amount = st.number_input("Amount to withdraw", min_value=100)
                submit_with = st.form_submit_button("Withdraw")
                if submit_with:
                    success, msg = make_withdrawal(st.session_state.user_id, with_amount)
                    if success:
                        st.success(msg + " ✅")
                    else:
                        st.error(msg + " ❌")
                        
        elif choice == "View your balance":
            st.subheader("Balance")
            bal = get_balance(st.session_state.user_id)
            st.info(f"Your balance is ₦{bal:,.2f}")
            
        elif choice == "View transaction history":
            st.subheader("Transaction History")
            history = get_transaction_history(st.session_state.user_id)
            if not history:
                st.info("No transactions yet.")
            else:
                df = pd.DataFrame(history, columns=["Type", "Amount", "Counterparty Name", "Counterparty Account", "Date"])
                df["Amount"] = df["Amount"].apply(lambda x: f"₦{x:,.2f}")
                st.dataframe(df)
                
        elif choice == "Make a transfer":
            st.subheader("Transfer")
            with st.form("transfer_form"):
                trans_account = st.text_input("Beneficiary Account Number")
                trans_amount = st.number_input("Amount to transfer", min_value=100)
                submit_trans = st.form_submit_button("Transfer")
                if submit_trans:
                    success, msg = make_transfer(st.session_state.user_id, trans_amount, trans_account.strip())
                    if success:
                        st.success(msg + " ✅")
                    else:
                        st.error(msg + " ❌")
                        
        elif choice == "View account details":
            st.subheader("Account Details")
            details = get_account_details(st.session_state.user_id)
            st.write(f"**Full Name:** {details[0]}")
            st.write(f"**Username:** {details[1]}")
            st.write(f"**Account Number:** {details[2]}")

if __name__ == "__main__":
    main()
