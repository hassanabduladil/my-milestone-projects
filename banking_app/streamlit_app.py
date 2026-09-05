import streamlit as st
import streamlit.components.v1 as components
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
            return True, user_id, f"Account created successfully! Your account number is {account_number}"
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
        return False, "Invalid username or password"

def get_balance(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()
        return row[0] if row else 0

def make_deposit(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        new_balance = balance + amount
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "deposit", amount, "Self Deposit", "Cash/Transfer"))
        conn.commit()

def make_withdrawal(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        balance = cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,)).fetchone()[0]
        if amount > balance:
            return False, "Insufficient funds in your account"
        new_balance = balance - amount
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "withdraw", amount, "ATM Cashout", "Self"))
        conn.commit()
        return True, f"Successfully withdrawn ₦{amount:,.2f}"

def make_transfer(user_id, amount, receiver_account):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        user = cursor.execute("SELECT full_name, balance, account_number FROM users WHERE id=?", (user_id,)).fetchone()
        receiver = cursor.execute("SELECT id, full_name, balance FROM users WHERE account_number = ?", (receiver_account,)).fetchone()
        
        if not receiver:
            return False, "Beneficiary account does not exist"
        if receiver_account == user[2]:
            return False, "You cannot transfer money to your own account"
        if amount > user[1]:
            return False, "Insufficient funds for this transfer"
            
        new_balance = user[1] - amount
        receiver_new_bal = receiver[2] + amount
        
        cursor.execute("UPDATE users SET balance = ? WHERE account_number = ?", (receiver_new_bal, receiver_account))
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
        
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (user_id, "Transfer", amount, receiver[1], receiver_account))
        cursor.execute("INSERT INTO transactions (user_id, type, amount, counterparty_name, counterparty_account) VALUES (?, ?, ?, ?, ?)", (receiver[0], "Transfer received", amount, user[0], user[2]))
        
        conn.commit()
        return True, f"Successfully transferred ₦{amount:,.2f} to {receiver[1]}"

def get_account_details(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT full_name, username, account_number FROM users WHERE id = ?", (user_id,)).fetchone()

def get_transaction_history(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        return cursor.execute("SELECT type, amount, counterparty_name, counterparty_account, timestamp FROM transactions WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()

# ----------------- CREATIVE JS & UI HELPERS -----------------

def trigger_confetti():
    """Lightweight pure JS celebratory confetti"""
    components.html("""
    <script>
    (function() {
        const colors = ['#6366f1', '#10b981', '#06b6d4', '#f59e0b', '#ec4899'];
        for (let i = 0; i < 40; i++) {
            const conf = document.createElement('div');
            conf.style.position = 'fixed';
            conf.style.left = Math.random() * 100 + 'vw';
            conf.style.top = '-10px';
            conf.style.width = (Math.random() * 8 + 6) + 'px';
            conf.style.height = (Math.random() * 12 + 8) + 'px';
            conf.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            conf.style.borderRadius = '3px';
            conf.style.zIndex = '999999';
            conf.style.pointerEvents = 'none';
            conf.style.opacity = Math.random() + 0.5;
            conf.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';
            conf.style.transition = 'top 2.2s cubic-bezier(0.25, 0.46, 0.45, 0.94), transform 2.2s ease-out, opacity 2.2s ease';
            document.body.appendChild(conf);

            setTimeout(() => {
                conf.style.top = (Math.random() * 50 + 60) + 'vh';
                conf.style.transform = 'rotate(' + (Math.random() * 720) + 'deg) scale(0.6)';
                conf.style.opacity = '0';
            }, 50);

            setTimeout(() => { conf.remove(); }, 2400);
        }
    })();
    </script>
    """, height=0)

def render_greeting_widget(username):
    """Dynamic local device greeting and live clock widget"""
    components.html(f"""
    <div style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        padding: 4px 2px;
    ">
        <div>
            <div id="greetingText" style="font-size: 1.35rem; font-weight: 800; color: #6366f1; letter-spacing: -0.5px;">
                Welcome back, {username}
            </div>
            <div id="liveClock" style="font-size: 0.82rem; color: #8892b0; margin-top: 3px; font-weight: 500;">
            </div>
        </div>
        <div style="
            display: flex;
            align-items: center;
            gap: 7px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.25);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.74rem;
            font-weight: 700;
            color: #10b981;
            letter-spacing: 0.5px;
        ">
            <span style="height: 7px; width: 7px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981;"></span>
            <span>SECURE ENCRYPTED</span>
        </div>
    </div>
    <script>
        function updateTime() {{
            const now = new Date();
            const hrs = now.getHours();
            let greet = "Good evening";
            if (hrs < 12) greet = "Good morning";
            else if (hrs < 17) greet = "Good afternoon";
            
            const dateStr = now.toLocaleDateString(undefined, {{ weekday: 'short', month: 'short', day: 'numeric' }});
            const timeStr = now.toLocaleTimeString(undefined, {{ hour: '2-digit', minute: '2-digit' }});
            
            document.getElementById("greetingText").innerHTML = greet + ", {username} 👋";
            document.getElementById("liveClock").innerHTML = "📅 " + dateStr + " • " + timeStr + " (Local)";
        }}
        updateTime();
        setInterval(updateTime, 30000);
    </script>
    """, height=65)

def render_copy_widget(account_number):
    """Interactive copy button with smooth toast feedback"""
    components.html(f"""
    <div style="display:flex; align-items:center; gap:12px; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
        <button id="copyBtn" onclick="copyAcc()" style="
            background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
            border: none;
            color: white;
            padding: 9px 18px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 7px;
            box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
            transition: all 0.2s ease;
        ">
            <span>📋 Copy Account Number</span>
        </button>
        <span id="copiedMsg" style="color: #10b981; font-size: 13px; font-weight: 700; display: none;">
            ✓ Copied to clipboard!
        </span>
    </div>
    <script>
    function copyAcc() {{
        navigator.clipboard.writeText('{account_number}').then(() => {{
            const msg = document.getElementById('copiedMsg');
            const btn = document.getElementById('copyBtn');
            btn.style.transform = 'scale(0.95)';
            setTimeout(() => btn.style.transform = 'scale(1)', 150);
            msg.style.display = 'inline';
            setTimeout(() => {{
                msg.style.display = 'none';
            }}, 2500);
        }}).catch(err => {{
            console.error(err);
        }});
    }}
    </script>
    """, height=45)

def render_virtual_card(full_name, account_number, balance):
    """Renders a sleek luxury Black Card interface"""
    formatted_acc = f"{account_number[:4]}  {account_number[4:]}"
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #090e17 0%, #1e1b4b 55%, #0d1527 100%);
        border-radius: 24px;
        padding: 24px 28px;
        color: white;
        box-shadow: 0 20px 45px -10px rgba(15, 23, 42, 0.65), 0 0 0 1px rgba(99, 102, 241, 0.25);
        margin: 10px 0 22px 0;
        position: relative;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <!-- Ambient decorative sheen -->
        <div style="
            position: absolute;
            top: -50px;
            right: -50px;
            width: 170px;
            height: 170px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        "></div>
        <div style="
            position: absolute;
            bottom: -40px;
            left: -40px;
            width: 150px;
            height: 150px;
            background: radial-gradient(circle, rgba(6, 182, 212, 0.25) 0%, transparent 70%);
            border-radius: 50%;
            pointer-events: none;
        "></div>

        <!-- Top Row: Card Brand & EMV Chip -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px;">
            <div style="display: flex; align-items: center; gap: 9px;">
                <div style="
                    background: linear-gradient(135deg, #6366f1, #06b6d4);
                    width: 30px;
                    height: 30px;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 900;
                    font-size: 15px;
                    color: white;
                    box-shadow: 0 4px 10px rgba(99, 102, 241, 0.4);
                ">▲</div>
                <div>
                    <span style="font-weight: 800; font-size: 15px; letter-spacing: 1.5px;">APEX</span>
                    <span style="font-weight: 500; font-size: 11px; opacity: 0.7; letter-spacing: 1.2px; margin-left: 5px;">PLATINUM</span>
                </div>
            </div>
            
            <!-- Metallic EMV Chip & NFC -->
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="
                    width: 40px;
                    height: 30px;
                    background: linear-gradient(135deg, #e5b558 0%, #f6d37d 50%, #c99335 100%);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    display: flex;
                    align-items: center;
                    justify-content: space-around;
                    padding: 2px 4px;
                    box-shadow: inset 0 0 4px rgba(0,0,0,0.35);
                ">
                    <div style="width: 1px; height: 100%; background: rgba(0,0,0,0.25);"></div>
                    <div style="width: 1px; height: 100%; background: rgba(0,0,0,0.25);"></div>
                </div>
                <span style="font-size: 19px; opacity: 0.85;">🛜</span>
            </div>
        </div>

        <!-- Middle: Balance -->
        <div style="margin-bottom: 22px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #a5b4fc; margin-bottom: 5px;">
                Total Available Balance
            </div>
            <div style="font-size: 2.15rem; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; text-shadow: 0 3px 12px rgba(0,0,0,0.4);">
                ₦{balance:,.2f}
            </div>
        </div>

        <!-- Bottom Row: Cardholder & Account Number -->
        <div style="display: flex; justify-content: space-between; align-items: flex-end; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.12);">
            <div>
                <div style="font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; opacity: 0.65;">
                    Cardholder
                </div>
                <div style="font-size: 14px; font-weight: 700; letter-spacing: 0.5px; margin-top: 2px;">
                    {full_name.upper()}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; opacity: 0.65;">
                    Account Number
                </div>
                <div style="font-size: 15px; font-weight: 700; font-family: monospace; letter-spacing: 2.2px; color: #38bdf8; margin-top: 2px;">
                    {formatted_acc}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def set_custom_css():
    st.markdown("""
        <style>
        /* Luxury Fintech Styling */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        /* Subtle ambient glow on the page */
        .stApp {
            background-image: radial-gradient(circle at 10% 8%, rgba(99, 102, 241, 0.07) 0%, transparent 45%),
                              radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.05) 0%, transparent 45%);
        }
        
        /* Headers */
        h1, h2, h3, h4 {
            color: var(--text-color) !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }

        /* App Action Cards (Buttons in Columns) */
        div.stButton > button {
            background: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid rgba(128, 128, 128, 0.16) !important;
            border-top: 4px solid #6366f1 !important;
            border-radius: 18px !important;
            padding: 14px 10px !important;
            font-size: 15px !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
            height: 105px !important;
            width: 100% !important;
            white-space: pre-line !important;
            line-height: 1.35 !important;
        }
        
        div.stButton > button:hover {
            border-top: 4px solid #06b6d4 !important;
            color: #6366f1 !important;
            transform: translateY(-4px) scale(1.01) !important;
            box-shadow: 0 12px 28px rgba(99, 102, 241, 0.18) !important;
        }

        /* Form Confirmation Buttons */
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #06b6d4 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            height: 50px !important;
            border: none !important;
            border-radius: 14px !important;
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
            transition: all 0.25s ease !important;
        }
        
        div[data-testid="stFormSubmitButton"] > button:hover {
            opacity: 0.93 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 25px rgba(79, 70, 229, 0.5) !important;
        }

        /* Modern Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: var(--secondary-background-color);
            padding: 5px;
            border-radius: 14px;
            border: 1px solid rgba(128, 128, 128, 0.15);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 8px 18px;
            color: var(--text-color);
            font-weight: 600;
            transition: all 0.2s ease;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
            color: #ffffff !important;
        }

        /* Input fields with sleek focus */
        div[data-baseweb="input"] {
            border-radius: 12px !important;
            border: 1px solid rgba(128, 128, 128, 0.25) !important;
        }

        div[data-baseweb="input"]:focus-within {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
        }

        /* Back button */
        .back-btn div.stButton > button {
            height: 44px !important;
            background: rgba(239, 68, 68, 0.12) !important;
            color: #ef4444 !important;
            border: 1px solid rgba(239, 68, 68, 0.3) !important;
            border-top: 1px solid rgba(239, 68, 68, 0.3) !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }
        
        .back-btn div.stButton > button:hover {
            background: #ef4444 !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
        }

        /* Logout button */
        .logout-btn div.stButton > button {
            height: 38px !important;
            background: rgba(128, 128, 128, 0.08) !important;
            border: 1px solid rgba(128, 128, 128, 0.25) !important;
            border-top: 1px solid rgba(128, 128, 128, 0.25) !important;
            border-radius: 20px !important;
            font-size: 13px !important;
            color: var(--text-color) !important;
            box-shadow: none !important;
        }

        .logout-btn div.stButton > button:hover {
            border-color: #ef4444 !important;
            color: #ef4444 !important;
            background: rgba(239, 68, 68, 0.08) !important;
            transform: scale(1.02) !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ----------------- MAIN APP CONTROLLER -----------------

def main():
    st.set_page_config(page_title="Apex Reserve Bank", page_icon="🏦", layout="centered")
    init_db()
    set_custom_css()

    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "current_operation" not in st.session_state:
        st.session_state.current_operation = None

    # Unauthenticated View (Login / Sign Up)
    if st.session_state.user_id is None:
        # Creative Hero Banner
        st.markdown("""
        <div style="text-align: center; padding: 25px 10px 15px 10px;">
            <div style="
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(6, 182, 212, 0.15));
                border: 1px solid rgba(99, 102, 241, 0.3);
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 12px;
                font-weight: 700;
                color: #6366f1;
                margin-bottom: 12px;
            ">
                <span>🛡️ NEXT-GEN DIGITAL BANKING</span>
            </div>
            <h1 style="font-size: 2.3rem; margin: 0 0 8px 0; background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Apex Reserve Bank
            </h1>
            <p style="font-size: 14px; color: #8892b0; max-width: 380px; margin: 0 auto;">
                Experience seamless payments, instant transfers, and institutional-grade security.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Sign In", "✨ Open Account"])
        
        with tab1:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            with st.form("login_form"):
                log_username = st.text_input("Username", placeholder="e.g. joshua_21")
                log_password = st.text_input("Password", type="password", placeholder="••••••••")
                submit_login = st.form_submit_button("Access My Account →", use_container_width=True)
                
                if submit_login:
                    if not log_username or not log_password:
                        st.error("Please provide both your username and password.")
                    else:
                        success, result = login(log_username, log_password)
                        if success:
                            st.session_state.user_id = result
                            st.session_state.username = log_username
                            st.rerun()
                        else:
                            st.error(result)
                            
        with tab2:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            
            # Interactive visual requirements card
            st.markdown("""
            <div style="
                background: var(--secondary-background-color);
                border: 1px solid rgba(99, 102, 241, 0.2);
                border-left: 4px solid #6366f1;
                border-radius: 14px;
                padding: 14px 18px;
                margin-bottom: 15px;
                font-size: 13px;
            ">
                <div style="font-weight: 700; color: #6366f1; margin-bottom: 6px;">📋 Account Verification Guidelines</div>
                <div style="opacity: 0.85; line-height: 1.5;">
                    • <b>Full Name:</b> At least 4 letters (hyphens & spaces allowed).<br>
                    • <b>Username:</b> 3–20 characters (letters, numbers, underscores).<br>
                    • <b>Password:</b> 8+ chars with uppercase, lowercase, digit & symbol.<br>
                    • <b>Opening Deposit:</b> Minimum opening capital is <b>₦2,000</b>.
                </div>
            </div>
            """, unsafe_allow_html=True)
                    
            with st.form("signup_form"):
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("First Name", placeholder="Abdul-Adil")
                with c2:
                    last_name = st.text_input("Last Name", placeholder="Hassan")
                    
                reg_username = st.text_input("Choose Username", placeholder="e.g. adil_apex")
                reg_password = st.text_input("Create Security Password", type="password", placeholder="8+ characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                initial_deposit = st.number_input("Initial Opening Deposit (₦)", min_value=0, value=2000, step=500)
                submit_signup = st.form_submit_button("Create My Account & Issue Card 💳", use_container_width=True)
                
                if submit_signup:
                    full_name = f"{first_name.strip().title()} {last_name.strip().title()}"
                    
                    if not first_name or not last_name:
                        st.error("First name and last name are required.")
                    elif len(full_name) < 4:
                        st.error("Full name must be at least 4 characters.")
                    elif not re.fullmatch(r"[A-Za-z \-]+", full_name):
                        st.error("Full name can only contain letters, spaces, and hyphens.")
                    elif not reg_username or len(reg_username) < 3 or len(reg_username) > 20 or not re.fullmatch(r"\w+", reg_username):
                        st.error("Username must be between 3 and 20 characters and contain only letters, numbers, and underscores.")
                    elif len(reg_password) < 8 or not re.search(r"[A-Z]", reg_password) or not re.search(r"[a-z]", reg_password) or not re.search(r"\d", reg_password) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", reg_password):
                        st.error("Password must be at least 8 characters long with uppercase, lowercase, number, and special character.")
                    elif reg_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif initial_deposit < 2000:
                        st.error("Minimum opening balance is ₦2,000.")
                    else:
                        success, user_id, msg = sign_up(full_name, reg_username, reg_password, int(initial_deposit))
                        if success:
                            st.session_state.user_id = user_id
                            st.session_state.username = reg_username
                            trigger_confetti()
                            st.rerun()
                        else:
                            st.error(msg)

    # Authenticated Dashboard View
    else:
        # User details
        details = get_account_details(st.session_state.user_id)
        if not details:
            st.session_state.user_id = None
            st.rerun()
            
        full_name, username, account_number = details
        current_balance = get_balance(st.session_state.user_id)

        # Dynamic JS Greeting & Clock
        render_greeting_widget(username)

        # Logout row
        logout_col1, logout_col2 = st.columns([4, 1])
        with logout_col2:
            st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
            if st.button("Log Out", key="logout_btn"):
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.current_operation = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # MAIN DASHBOARD VIEW
        if st.session_state.current_operation is None:
            # Render Virtual Platinum Card
            render_virtual_card(full_name, account_number, current_balance)

            # Operations Grid Title
            st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 15px 0 10px 0;">
                <span style="font-weight: 800; font-size: 1.1rem; letter-spacing: -0.3px;">Core Operations</span>
                <span style="font-size: 12px; color: #6366f1; font-weight: 600;">24/7 Fast Settlement</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Cards in 2 Columns
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Deposit\nAdd Funds", use_container_width=True, key="op_dep"):
                    st.session_state.current_operation = "deposit"
                    st.rerun()
                if st.button("⚡ Transfer\nSend Money", use_container_width=True, key="op_trans"):
                    st.session_state.current_operation = "transfer"
                    st.rerun()
                if st.button("📜 History\nTransactions", use_container_width=True, key="op_hist"):
                    st.session_state.current_operation = "history"
                    st.rerun()
            with col2:
                if st.button("🏧 Withdraw\nCash Payout", use_container_width=True, key="op_with"):
                    st.session_state.current_operation = "withdraw"
                    st.rerun()
                if st.button("📊 Balance\nLive Breakdown", use_container_width=True, key="op_bal"):
                    st.session_state.current_operation = "balance"
                    st.rerun()
                if st.button("👤 Account\nCard & Limits", use_container_width=True, key="op_det"):
                    st.session_state.current_operation = "details"
                    st.rerun()
                    
        # SPECIFIC OPERATION VIEWS
        else:
            # Back to Dashboard Button
            st.markdown("<div class='back-btn' style='margin-bottom: 15px;'>", unsafe_allow_html=True)
            if st.button("⬅ Back to Dashboard"):
                st.session_state.current_operation = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
            op = st.session_state.current_operation
            
            # DEPOSIT
            if op == "deposit":
                st.markdown("### 📥 Deposit Funds")
                st.markdown("<p style='font-size: 13px; color: #8892b0;'>Instant credit into your Apex Reserve account.</p>", unsafe_allow_html=True)
                
                with st.form("deposit_form"):
                    dep_amount = st.number_input("Enter Amount to Deposit (₦)", min_value=100, step=500, value=1000)
                    submit_dep = st.form_submit_button("Confirm & Deposit Funds →", use_container_width=True)
                    if submit_dep:
                        make_deposit(st.session_state.user_id, dep_amount)
                        trigger_confetti()
                        st.success(f"Deposit Successful! ₦{dep_amount:,.2f} added to your account. ✅")
                        
            # WITHDRAW
            elif op == "withdraw":
                st.markdown("### 🏧 Withdraw Cash")
                st.markdown(f"<p style='font-size: 13px; color: #8892b0;'>Available to withdraw: <b>₦{current_balance:,.2f}</b></p>", unsafe_allow_html=True)
                
                with st.form("withdraw_form"):
                    with_amount = st.number_input("Enter Amount to Withdraw (₦)", min_value=100, step=500, value=500)
                    submit_with = st.form_submit_button("Confirm Withdrawal →", use_container_width=True)
                    if submit_with:
                        success, msg = make_withdrawal(st.session_state.user_id, with_amount)
                        if success:
                            st.success(msg + " ✅")
                        else:
                            st.error(msg + " ❌")
                            
            # BALANCE
            elif op == "balance":
                st.markdown("### 📊 Account Financial Summary")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    st.metric(label="Liquid Balance", value=f"₦{current_balance:,.2f}")
                with col_b2:
                    st.metric(label="Daily Outflow Limit", value="₦5,000,000.00")
                
                st.markdown("""
                <div style="
                    background: var(--secondary-background-color);
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    border-radius: 16px;
                    padding: 16px 20px;
                    margin-top: 15px;
                ">
                    <div style="font-weight: 700; color: #6366f1; margin-bottom: 8px;">Apex Yield & Security</div>
                    <div style="font-size: 13px; opacity: 0.85; line-height: 1.6;">
                        • Annual APY Accrual: <b>8.5% p.a.</b><br>
                        • Deposit Insurance: <b>NDIC / Simulation Protected</b><br>
                        • Inflow Channel: Instant NIBSS / Internal Wire
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # TRANSACTION HISTORY
            elif op == "history":
                st.markdown("### 📜 Transaction Activity")
                history = get_transaction_history(st.session_state.user_id)
                
                if not history:
                    st.info("No recorded transactions yet. Make a deposit or transfer to see your history.")
                else:
                    # Render sleek custom activity cards
                    for t in history:
                        t_type, amount, cp_name, cp_acc, t_time = t
                        is_credit = t_type.lower() in ["deposit", "transfer received", "transfer recieved"]
                        badge_bg = "rgba(16, 185, 129, 0.15)" if is_credit else "rgba(244, 63, 94, 0.15)"
                        badge_color = "#10b981" if is_credit else "#f43f5e"
                        arrow = "↓" if is_credit else "↑"
                        sign = "+" if is_credit else "-"
                        
                        desc = cp_name if cp_name and cp_name != "NULL" else ("Cash Inflow" if is_credit else "Withdrawal")
                        acc_desc = f" • Acc: {cp_acc}" if cp_acc and cp_acc != "NULL" else ""

                        st.markdown(f"""
                        <div style="
                            background: var(--secondary-background-color);
                            border: 1px solid rgba(128, 128, 128, 0.15);
                            border-radius: 14px;
                            padding: 14px 18px;
                            margin-bottom: 10px;
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                        ">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="
                                    width: 38px;
                                    height: 38px;
                                    border-radius: 10px;
                                    background: {badge_bg};
                                    color: {badge_color};
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 18px;
                                    font-weight: 800;
                                ">{arrow}</div>
                                <div>
                                    <div style="font-weight: 700; font-size: 14px; color: var(--text-color);">{t_type.capitalize()}</div>
                                    <div style="font-size: 12px; color: #8892b0; margin-top: 1px;">{desc}{acc_desc}</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-weight: 800; font-size: 15px; color: {badge_color};">
                                    {sign}₦{amount:,.2f}
                                </div>
                                <div style="font-size: 11px; color: #8892b0; margin-top: 1px;">{t_time}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Expandable Raw Dataframe Table
                    with st.expander("🔍 View Raw Spreadsheet Table"):
                        df = pd.DataFrame(history, columns=["Type", "Amount", "Counterparty", "Account", "Timestamp"])
                        df["Amount"] = df["Amount"].apply(lambda x: f"₦{x:,.2f}")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    
            # TRANSFER
            elif op == "transfer":
                st.markdown("### ⚡ Instant Transfer")
                st.markdown(f"<p style='font-size: 13px; color: #8892b0;'>Send funds instantly. Available balance: <b>₦{current_balance:,.2f}</b></p>", unsafe_allow_html=True)
                
                with st.form("transfer_form"):
                    trans_account = st.text_input("Beneficiary 8-Digit Account Number", placeholder="e.g. 12345678")
                    trans_amount = st.number_input("Amount to Transfer (₦)", min_value=100, step=500, value=1000)
                    submit_trans = st.form_submit_button("Authorize & Send Money →", use_container_width=True)
                    
                    if submit_trans:
                        success, msg = make_transfer(st.session_state.user_id, trans_amount, trans_account.strip())
                        if success:
                            trigger_confetti()
                            st.success(msg + " ✅")
                        else:
                            st.error(msg + " ❌")
                            
            # ACCOUNT DETAILS & CARD
            elif op == "details":
                st.markdown("### 👤 Account Profile & Card")
                
                # Render the Virtual Card
                render_virtual_card(full_name, account_number, current_balance)
                
                # Interactive Copy Account Widget
                render_copy_widget(account_number)
                
                st.markdown(f"""
                <div style="
                    background: var(--secondary-background-color);
                    border: 1px solid rgba(128, 128, 128, 0.2);
                    border-radius: 16px;
                    padding: 20px;
                    margin-top: 15px;
                ">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(128,128,128,0.15); padding-bottom: 10px;">
                        <span style="color: #8892b0; font-size: 13px;">Full Legal Name</span>
                        <span style="font-weight: 700; font-size: 14px;">{full_name}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(128,128,128,0.15); padding: 10px 0;">
                        <span style="color: #8892b0; font-size: 13px;">Username Tag</span>
                        <span style="font-weight: 700; font-size: 14px; color: #6366f1;">@{username}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid rgba(128,128,128,0.15); padding: 10px 0;">
                        <span style="color: #8892b0; font-size: 13px;">Account Tier</span>
                        <span style="font-weight: 700; font-size: 14px; color: #10b981;">Apex Black (Tier 3)</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding-top: 10px;">
                        <span style="color: #8892b0; font-size: 13px;">Daily Limit</span>
                        <span style="font-weight: 700; font-size: 14px;">₦5,000,000.00</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
