import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import os
import hashlib
import binascii
from datetime import datetime
from functools import partial

DB_FILE = 'atm.db'
ADMIN_PASSWORD = 'admin123'  # change this before deploying
LOCALES = {
    'en': {
        'title': 'Python ATM',
        'create_acc': 'Create Account',
        'login': 'Login',
        'admin': 'Admin',
        'acc_no': 'Account Number',
        'name': 'Name',
        'pin': 'PIN',
        'initial_deposit': 'Initial deposit',
        'submit': 'Submit',
        'balance': 'Balance',
        'deposit': 'Deposit',
        'withdraw': 'Withdraw',
        'transfer': 'Transfer',
        'mini_stmt': 'Mini-statement',
        'change_pin': 'Change PIN',
        'logout': 'Logout',
        'amount': 'Amount',
        'to_acc': 'To account',
        'reset_pin': 'Reset PIN',
        'view_accounts': 'View Accounts',
        'admin_login': 'Admin Login',

    }
}

# Choose locale and currency symbol here
LOCALE = 'en'  # 'en' or 'hi'
CURRENCY = '₹'

L = LOCALES[LOCALE]

# --- DB / Crypto utilities ---

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        acc_no TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        pin_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        balance REAL NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acc_no TEXT NOT NULL,
        time TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        balance REAL NOT NULL,
        note TEXT
    )
    ''')
    conn.commit()
    conn.close()


def timestamp():
    return datetime.now().isoformat(sep=' ', timespec='seconds')


def generate_salt() -> bytes:
    return os.urandom(16)


def hash_pin(pin: str, salt: bytes) -> str:
    # PBKDF2-HMAC-SHA256
    dk = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 150_000)
    return binascii.hexlify(dk).decode('ascii')


def store_account(acc_no: str, name: str, pin: str, initial: float):
    salt = generate_salt()
    pin_hash = hash_pin(pin, salt)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO accounts (acc_no, name, pin_hash, salt, balance) VALUES (?, ?, ?, ?, ?)',
                (acc_no, name, pin_hash, binascii.hexlify(salt).decode('ascii'), round(initial, 2)))
    conn.commit()
    add_transaction_db(acc_no, 'deposit', initial, round(initial, 2), 'Initial deposit')
    conn.close()


def get_account(acc_no: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT acc_no, name, pin_hash, salt, balance FROM accounts WHERE acc_no = ?', (acc_no,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {'acc_no': row[0], 'name': row[1], 'pin_hash': row[2], 'salt': row[3], 'balance': row[4]}
    return None


def update_balance(acc_no: str, new_balance: float):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE accounts SET balance = ? WHERE acc_no = ?', (round(new_balance,2), acc_no))
    conn.commit()
    conn.close()


def add_transaction_db(acc_no: str, ttype: str, amount: float, balance: float, note: str = ''):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO transactions (acc_no, time, type, amount, balance, note) VALUES (?, ?, ?, ?, ?, ?)',
                (acc_no, timestamp(), ttype, amount, round(balance,2), note))
    conn.commit()
    conn.close()


def get_transactions(acc_no: str, limit: int = 10):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT time, type, amount, balance, note FROM transactions WHERE acc_no = ? ORDER BY id DESC LIMIT ?', (acc_no, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def list_accounts():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT acc_no, name, balance FROM accounts')
    rows = cur.fetchall()
    conn.close()
    return rows


def reset_pin_db(acc_no: str, new_pin: str):
    salt = generate_salt()
    pin_hash = hash_pin(new_pin, salt)
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE accounts SET pin_hash = ?, salt = ? WHERE acc_no = ?', (pin_hash, binascii.hexlify(salt).decode('ascii'), acc_no))
    conn.commit()
    conn.close()

# --- Tkinter GUI ---

class ATMApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(L['title'])
        self.geometry('480x360')
        self.resizable(False, False)
        self.current_acc = None
        self.create_main_menu()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def create_main_menu(self):
        self.clear()
        tk.Label(self, text=L['title'], font=('Arial', 18, 'bold')).pack(pady=10)
        tk.Button(self, text=L['create_acc'], width=20, command=self.create_account_ui).pack(pady=6)
        tk.Button(self, text=L['login'], width=20, command=self.login_ui).pack(pady=6)
        tk.Button(self, text=L['admin'], width=20, command=self.admin_login_ui).pack(pady=6)
        tk.Button(self, text='Exit', width=20, command=self.quit).pack(pady=6)

    # --- Create account UI ---
    def create_account_ui(self):
        self.clear()
        tk.Label(self, text=L['create_acc'], font=('Arial', 14)).pack(pady=6)
        frm = tk.Frame(self)
        frm.pack(pady=6)
        tk.Label(frm, text=L['acc_no']).grid(row=0, column=0, sticky='e')
        acc_entry = tk.Entry(frm)
        acc_entry.grid(row=0, column=1)
        tk.Label(frm, text=L['name']).grid(row=1, column=0, sticky='e')
        name_entry = tk.Entry(frm)
        name_entry.grid(row=1, column=1)
        tk.Label(frm, text=L['pin']).grid(row=2, column=0, sticky='e')
        pin_entry = tk.Entry(frm, show='*')
        pin_entry.grid(row=2, column=1)
        tk.Label(frm, text=L['initial_deposit']).grid(row=3, column=0, sticky='e')
        initial_entry = tk.Entry(frm)
        initial_entry.grid(row=3, column=1)

        def submit():
            acc_no = acc_entry.get().strip()
            name = name_entry.get().strip()
            pin = pin_entry.get().strip()
            try:
                initial = float(initial_entry.get().strip() or 0.0)
            except ValueError:
                messagebox.showerror('Error', 'Invalid initial deposit')
                return
            if not acc_no.isdigit():
                messagebox.showerror('Error', 'Account number must be numeric')
                return
            if get_account(acc_no):
                messagebox.showerror('Error', 'Account number already exists')
                return
            if not (pin.isdigit() and 4 <= len(pin) <= 6):
                messagebox.showerror('Error', 'PIN must be 4-6 digits')
                return
            store_account(acc_no, name or 'Unnamed', pin, initial)
            messagebox.showinfo('Success', f'Account {acc_no} created')
            self.create_main_menu()

        tk.Button(self, text=L['submit'], command=submit).pack(pady=6)
        tk.Button(self, text='Back', command=self.create_main_menu).pack()

    # --- Login UI ---
    def login_ui(self):
        self.clear()
        tk.Label(self, text=L['login'], font=('Arial', 14)).pack(pady=6)
        frm = tk.Frame(self)
        frm.pack(pady=6)
        tk.Label(frm, text=L['acc_no']).grid(row=0, column=0, sticky='e')
        acc_entry = tk.Entry(frm)
        acc_entry.grid(row=0, column=1)
        tk.Label(frm, text=L['pin']).grid(row=1, column=0, sticky='e')
        pin_entry = tk.Entry(frm, show='*')
        pin_entry.grid(row=1, column=1)

        def submit():
            acc_no = acc_entry.get().strip()
            pin = pin_entry.get().strip()
            acct = get_account(acc_no)
            if not acct:
                messagebox.showerror('Error', 'Account not found')
                return
            salt = binascii.unhexlify(acct['salt'])
            if hash_pin(pin, salt) == acct['pin_hash']:
                self.current_acc = acc_no
                self.account_menu()
            else:
                messagebox.showerror('Error', 'Incorrect PIN')

        tk.Button(self, text=L['submit'], command=submit).pack(pady=6)
        tk.Button(self, text='Back', command=self.create_main_menu).pack()

    # --- Account menu ---
    def account_menu(self):
        self.clear()
        acct = get_account(self.current_acc)
        tk.Label(self, text=f"{acct['name']} ({acct['acc_no']})", font=('Arial', 14)).pack(pady=6)
        tk.Label(self, text=f"{L['balance']}: {CURRENCY}{acct['balance']:.2f}").pack(pady=6)
        tk.Button(self, text=L['deposit'], width=20, command=self.deposit_ui).pack(pady=4)
        tk.Button(self, text=L['withdraw'], width=20, command=self.withdraw_ui).pack(pady=4)
        tk.Button(self, text=L['transfer'], width=20, command=self.transfer_ui).pack(pady=4)
        tk.Button(self, text=L['mini_stmt'], width=20, command=self.mini_statement_ui).pack(pady=4)
        tk.Button(self, text=L['change_pin'], width=20, command=self.change_pin_ui).pack(pady=4)
        tk.Button(self, text=L['logout'], width=20, command=self.logout).pack(pady=8)

    def logout(self):
        self.current_acc = None
        self.create_main_menu()

    # --- Deposit / Withdraw / Transfer / Statements ---
    def deposit_ui(self):
        amt = simpledialog.askfloat(L['deposit'], L['amount'])
        if amt is None:
            return
        if amt <= 0:
            messagebox.showerror('Error', 'Amount must be positive')
            return
        acct = get_account(self.current_acc)
        new_bal = acct['balance'] + amt
        update_balance(self.current_acc, new_bal)
        add_transaction_db(self.current_acc, 'deposit', amt, new_bal, 'Cash deposit')
        messagebox.showinfo('Success', f'Deposited {CURRENCY}{amt:.2f} New balance: {CURRENCY}{new_bal:.2f}')
        self.account_menu()

    def withdraw_ui(self):
        amt = simpledialog.askfloat(L['withdraw'], L['amount'])
        if amt is None:
            return
        if amt <= 0:
            messagebox.showerror('Error', 'Amount must be positive')
            return
        acct = get_account(self.current_acc)
        if amt > acct['balance']:
            messagebox.showerror('Error', 'Insufficient funds')
            return
        new_bal = acct['balance'] - amt
        update_balance(self.current_acc, new_bal)
        add_transaction_db(self.current_acc, 'withdraw', -amt, new_bal, 'Cash withdrawal')
        messagebox.showinfo('Success', f'Withdrawn {CURRENCY}{amt:.2f} New balance: {CURRENCY}{new_bal:.2f}')
        self.account_menu()

    def transfer_ui(self):
        to_acc = simpledialog.askstring(L['transfer'], L['to_acc'])
        if to_acc is None:
            return
        if to_acc == self.current_acc:
            messagebox.showerror('Error', 'Cannot transfer to same account')
            return
        if not get_account(to_acc):
            messagebox.showerror('Error', 'Recipient account not found')
            return
        amt = simpledialog.askfloat(L['transfer'], L['amount'])
        if amt is None:
            return
        if amt <= 0:
            messagebox.showerror('Error', 'Amount must be positive')
            return
        acct = get_account(self.current_acc)
        if amt > acct['balance']:
            messagebox.showerror('Error', 'Insufficient funds')
            return
        new_bal_from = acct['balance'] - amt
        acct_to = get_account(to_acc)
        new_bal_to = acct_to['balance'] + amt
        update_balance(self.current_acc, new_bal_from)
        update_balance(to_acc, new_bal_to)
        add_transaction_db(self.current_acc, 'transfer_out', -amt, new_bal_from, f'Transfer to {to_acc}')
        add_transaction_db(to_acc, 'transfer_in', amt, new_bal_to, f'Transfer from {self.current_acc}')
        messagebox.showinfo('Success', f'Transferred {CURRENCY}{amt:.2f} to {to_acc}')
        self.account_menu()

    def mini_statement_ui(self):
        rows = get_transactions(self.current_acc, limit=10)
        if not rows:
            messagebox.showinfo('Mini-statement', 'No transactions yet')
            return
        txt = ''
        for r in rows:
            txt += f"{r[0]} | {r[1]:12} | {r[2]:8.2f} | bal: {CURRENCY}{r[3]:8.2f} | {r[4]}"
        # show in a simple scrollable window
        win = tk.Toplevel(self)
        win.title(L['mini_stmt'])
        txtw = tk.Text(win, width=80, height=20)
        txtw.pack()
        txtw.insert('1.0', txt)
        txtw.config(state='disabled')

    def change_pin_ui(self):
        old = simpledialog.askstring(L['change_pin'], 'Current PIN', show='*')
        if old is None:
            return
        acct = get_account(self.current_acc)
        salt = binascii.unhexlify(acct['salt'])
        if hash_pin(old, salt) != acct['pin_hash']:
            messagebox.showerror('Error', 'Incorrect current PIN')
            return
        new_pin = simpledialog.askstring(L['change_pin'], 'New PIN (4-6 digits)', show='*')
        if new_pin is None:
            return
        if not (new_pin.isdigit() and 4 <= len(new_pin) <= 6):
            messagebox.showerror('Error', 'PIN must be 4-6 digits')
            return
        reset_pin_db(self.current_acc, new_pin)
        messagebox.showinfo('Success', 'PIN changed')

    # --- Admin ---
    def admin_login_ui(self):
        pwd = simpledialog.askstring(L['admin_login'], 'Admin password', show='*')
        if pwd is None:
            return
        if pwd != ADMIN_PASSWORD:
            messagebox.showerror('Error', 'Incorrect admin password')
            return
        self.admin_menu()

    def admin_menu(self):
        self.clear()
        tk.Label(self, text='Admin Panel', font=('Arial', 16)).pack(pady=6)
        tk.Button(self, text=L['view_accounts'], width=25, command=self.view_accounts_ui).pack(pady=4)
        tk.Button(self, text=L['reset_pin'], width=25, command=self.admin_reset_pin_ui).pack(pady=4)
        tk.Button(self, text='Back', width=25, command=self.create_main_menu).pack(pady=8)

    def view_accounts_ui(self):
        rows = list_accounts()
        if not rows:
            messagebox.showinfo('Accounts', 'No accounts found')
            return
        win = tk.Toplevel(self)
        win.title('Accounts')
        txt = tk.Text(win, width=60, height=20)
        txt.pack()
        for r in rows:
            txt.insert('end', f"{r[0]} | {r[1]} | {CURRENCY}{r[2]:.2f}")
        txt.config(state='disabled')

    def admin_reset_pin_ui(self):
        acc_no = simpledialog.askstring(L['reset_pin'], L['acc_no'])
        if acc_no is None:
            return
        if not get_account(acc_no):
            messagebox.showerror('Error', 'Account not found')
            return
        new_pin = simpledialog.askstring(L['reset_pin'], 'Enter new PIN (4-6 digits)')
        if new_pin is None:
            return
        if not (new_pin.isdigit() and 4 <= len(new_pin) <= 6):
            messagebox.showerror('Error', 'PIN must be 4-6 digits')
            return
        reset_pin_db(acc_no, new_pin)
        messagebox.showinfo('Success', f'PIN for {acc_no} reset')


if __name__ == '__main__':
    init_db()

    app = ATMApp()
    app.mainloop()
