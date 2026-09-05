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
            user_id = cursor.lastrowid
            conn.commit()
            return True, user_id, f"Account created successfully. Your account number is {account_number}"
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, None, "Username is already taken"
            elif "account_number" in str(e):
                return False, None, "Account number already exists"
            else:
                return False, None, "A user with those details already exists"

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

def set_custom_css():
    st.markdown("""
        <style>
        /* Modern App styling & layout tweaks */
        
        /* Headers dynamic color */
        h1, h2, h3, h4 {
            color: var(--primary-color) !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }
        
        /* Dashboard buttons to look like modern app cards */
        div.stButton > button {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            border: 1px solid rgba(128, 128, 128, 0.15);
            border-top: 4px solid #3b82f6; /* beautiful blue accent */
            border-radius: 16px;
            padding: 15px 10px;
            font-size: 17px;
            font-weight: 700;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            height: 110px;
            width: 100%;
        }
        
        div.stButton > button:hover {
            border-top: 4px solid #8b5cf6; /* purple accent on hover */
            color: #8b5cf6 !important;
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        }

        /* Specific back button style override */
        .back-btn div.stButton > button {
            height: 50px;
            background-color: #ef4444 !important;
            color: white !important;
            border: none;
            border-top: none;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(239, 68, 68, 0.3);
        }
        
        .back-btn div.stButton > button:hover {
            background-color: #dc2626 !important;
            color: white !important;
            transform: translateY(-2px);
        }

        /* Specific logout button style override */
        .logout-btn div.stButton > button {
            height: 45px;
            background-color: transparent !important;
            color: var(--text-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-top: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 20px;
            box-shadow: none;
            font-size: 14px;
        }

        .logout-btn div.stButton > button:hover {
            background-color: rgba(239, 68, 68, 0.1) !important;
            color: #ef4444 !important;
            border-color: #ef4444 !important;
            transform: scale(1.02);
        }

        /* Input fields rounded styling */
        div[data-baseweb="input"] {
            border-radius: 12px;
        }

        /* Prevent columns from wrapping to lists on mobile screens (< 600px) */
        @media (max-width: 600px) {
            div[data-testid="stHorizontalBlock"] {
                flex-wrap: nowrap !important;
                gap: 12px !important;
            }
            div[data-testid="column"] {
                width: 50% !important;
                flex: 1 1 calc(50% - 12px) !important;
                min-width: calc(50% - 12px) !important;
            }
            div.stButton > button {
                font-size: 14px !important;
                height: 95px !important;
                padding: 10px 5px !important;
            }
        }
        
        </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Apex Bank", page_icon="🏦", layout="centered")
    init_db()
    set_custom_css()

    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "current_operation" not in st.session_state:
        st.session_state.current_operation = None

    if st.session_state.user_id is None:
        st.markdown("<h1 style='text-align: center; color: var(--primary-color);'>🏦 Apex Bank</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])
        
        with tab1:
            st.header("Welcome Back")
            with st.form("login_form"):
                log_username = st.text_input("Username")
                log_password = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Log In", use_container_width=True)
                
                if submit_login:
                    if not log_username or not log_password:
                        st.error("Please fill in all fields")
                    else:
                        success, result = login(log_username, log_password)
                        if success:
                            st.session_state.user_id = result
                            st.session_state.username = log_username
                            st.rerun()
                        else:
                            st.error(result)
                            
        with tab2:
            st.header("Create an Account")
            st.info("💡 **Requirements:**\n"
                    "- **Name**: Must be at least 4 characters long and contain only letters, spaces, or hyphens.\n"
                    "- **Username**: 3-20 characters, containing only letters, numbers, and underscores.\n"
                    "- **Password**: At least 8 characters, with 1 uppercase, 1 lowercase, 1 number, and 1 special character.\n"
                    "- **Deposit**: Minimum opening balance is ₦2,000.")
                    
            with st.form("signup_form"):
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                reg_username = st.text_input("Username")
                reg_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                initial_deposit = st.number_input("Initial Deposit (₦)", min_value=0)
                submit_signup = st.form_submit_button("Sign Up", use_container_width=True)
                
                if submit_signup:
                    full_name = f"{first_name.strip().title()} {last_name.strip().title()}"
                    
                    if not first_name or not last_name:
                        st.error("First name and last name cannot be empty.")
                    elif len(full_name) < 4:
                        st.error("Full name must be at least 4 characters.")
                    elif not re.fullmatch(r"[A-Za-z \-]+", full_name):
                        st.error("Full name must contain only letters, spaces, and hyphens.")
                    elif not reg_username or len(reg_username) < 3 or len(reg_username) > 20 or not re.fullmatch(r"\w+", reg_username):
                        st.error("Username must be between 3 and 20 characters and contain only letters, numbers, and underscores.")
                    elif len(reg_password) < 8 or not re.search(r"[A-Z]", reg_password) or not re.search(r"[a-z]", reg_password) or not re.search(r"\d", reg_password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", reg_password):
                        st.error("Password does not meet the requirements.")
                    elif reg_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif initial_deposit < 2000:
                        st.error("Minimum opening balance is ₦2,000.")
                    else:
                        success, user_id, msg = sign_up(full_name, reg_username, reg_password, int(initial_deposit))
                        if success:
                            st.session_state.user_id = user_id
                            st.session_state.username = reg_username
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
    else:
        # Dashboard Header
        col_title, col_logout = st.columns([3, 1])
        with col_title:
            st.title(f"Hello, {st.session_state.username} 👋")
        with col_logout:
            st.write("") # spacing
            st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
            if st.button("Log Out", key="logout"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.current_operation = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        if st.session_state.current_operation is None:
            # Home Dashboard view
            st.markdown("### What would you like to do?")
            
            # Show balance sneak peek
            bal = get_balance(st.session_state.user_id)
            st.info(f"**Available Balance:** ₦{bal:,.2f}")
            
            # Grid of operations
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💰 Deposit", use_container_width=True):
                    st.session_state.current_operation = "deposit"
                    st.rerun()
                if st.button("💸 Transfer", use_container_width=True):
                    st.session_state.current_operation = "transfer"
                    st.rerun()
                if st.button("📜 Transaction History", use_container_width=True):
                    st.session_state.current_operation = "history"
                    st.rerun()
            with col2:
                if st.button("💳 Withdraw", use_container_width=True):
                    st.session_state.current_operation = "withdraw"
                    st.rerun()
                if st.button("🏦 View Balance", use_container_width=True):
                    st.session_state.current_operation = "balance"
                    st.rerun()
                if st.button("👤 Account Details", use_container_width=True):
                    st.session_state.current_operation = "details"
                    st.rerun()
                    
        else:
            # Show back button
            st.markdown("<div class='back-btn'>", unsafe_allow_html=True)
            if st.button("⬅ Back to Dashboard"):
                st.session_state.current_operation = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            st.write("---")
            
            # Operation views
            op = st.session_state.current_operation
            
            if op == "deposit":
                st.subheader("💰 Make a Deposit")
                with st.form("deposit_form"):
                    dep_amount = st.number_input("Amount to deposit (₦)", min_value=100)
                    submit_dep = st.form_submit_button("Confirm Deposit", use_container_width=True)
                    if submit_dep:
                        make_deposit(st.session_state.user_id, dep_amount)
                        st.success("Deposit Successful ✅")
                        
            elif op == "withdraw":
                st.subheader("💳 Make a Withdrawal")
                with st.form("withdraw_form"):
                    with_amount = st.number_input("Amount to withdraw (₦)", min_value=100)
                    submit_with = st.form_submit_button("Confirm Withdrawal", use_container_width=True)
                    if submit_with:
                        success, msg = make_withdrawal(st.session_state.user_id, with_amount)
                        if success:
                            st.success(msg + " ✅")
                        else:
                            st.error(msg + " ❌")
                            
            elif op == "balance":
                st.subheader("🏦 Your Balance")
                bal = get_balance(st.session_state.user_id)
                st.metric(label="Current Balance", value=f"₦{bal:,.2f}")
                
            elif op == "history":
                st.subheader("📜 Transaction History")
                history = get_transaction_history(st.session_state.user_id)
                if not history:
                    st.info("No transactions yet.")
                else:
                    df = pd.DataFrame(history, columns=["Type", "Amount", "Counterparty Name", "Counterparty Account", "Date"])
                    df["Amount"] = df["Amount"].apply(lambda x: f"₦{x:,.2f}")
                    # Format date
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d %H:%M')
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
            elif op == "transfer":
                st.subheader("💸 Make a Transfer")
                with st.form("transfer_form"):
                    trans_account = st.text_input("Beneficiary Account Number")
                    trans_amount = st.number_input("Amount to transfer (₦)", min_value=100)
                    submit_trans = st.form_submit_button("Confirm Transfer", use_container_width=True)
                    if submit_trans:
                        success, msg = make_transfer(st.session_state.user_id, trans_amount, trans_account.strip())
                        if success:
                            st.success(msg + " ✅")
                        else:
                            st.error(msg + " ❌")
                            
            elif op == "details":
                st.subheader("👤 Account Details")
                details = get_account_details(st.session_state.user_id)
                
                st.markdown(f"""
                <div style="background-color: var(--secondary-background-color); color: var(--text-color); padding: 20px; border-radius: 12px; border: 1px solid var(--primary-color); box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <h4 style="margin-top:0; color: var(--primary-color);">{details[0]}</h4>
                    <p style="font-size: 14px;"><b>Username:</b> @{details[1]}</p>
                    <hr style="margin: 10px 0; border-color: rgba(128, 128, 128, 0.2);">
                    <p style="margin-bottom:0; font-size: 18px;"><b>Account Number:</b> <code style="font-size: 18px;">{details[2]}</code></p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
