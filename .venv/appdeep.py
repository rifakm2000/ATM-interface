import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import datetime

class ATMInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("ATM Machine")
        self.root.geometry("400x500")
        self.root.configure(bg='#2C3E50')
        
        # Initialize database
        self.init_database()
        
        # Current user session
        self.current_user = None
        self.current_account = None
        
        # Create GUI elements
        self.create_login_screen()
    
    def init_database(self):
        """Initialize the database with sample accounts"""
        self.conn = sqlite3.connect('atm_database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create accounts table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_number TEXT PRIMARY KEY,
                pin TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                name TEXT NOT NULL
            )
        ''')
        
        # Create transaction history table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (account_number) REFERENCES accounts (account_number)
            )
        ''')
        
        # Insert sample accounts if none exist
        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        if self.cursor.fetchone()[0] == 0:
            sample_accounts = [
                ('123456789', '1234', 5000.00, 'John Doe'),
                ('987654321', '4321', 3000.00, 'Jane Smith'),
                ('555555555', '5555', 10000.00, 'Bob Johnson')
            ]
            self.cursor.executemany(
                "INSERT INTO accounts (account_number, pin, balance, name) VALUES (?, ?, ?, ?)",
                sample_accounts
            )
            self.conn.commit()
    
    def create_login_screen(self):
        """Create the login screen"""
        self.clear_screen()
        
        # Title
        title_label = tk.Label(self.root, text="ATM MACHINE", font=('Arial', 20, 'bold'), 
                              bg='#2C3E50', fg='#ECF0F1')
        title_label.pack(pady=20)
        
        # Account number entry
        acc_frame = tk.Frame(self.root, bg='#2C3E50')
        acc_frame.pack(pady=10)
        tk.Label(acc_frame, text="Account Number:", font=('Arial', 12), 
                bg='#2C3E50', fg='#ECF0F1').pack(side=tk.LEFT)
        self.acc_entry = tk.Entry(acc_frame, font=('Arial', 12), show="")
        self.acc_entry.pack(side=tk.LEFT, padx=10)
        
        # PIN entry
        pin_frame = tk.Frame(self.root, bg='#2C3E50')
        pin_frame.pack(pady=10)
        tk.Label(pin_frame, text="PIN:", font=('Arial', 12), 
                bg='#2C3E50', fg='#ECF0F1').pack(side=tk.LEFT)
        self.pin_entry = tk.Entry(pin_frame, font=('Arial', 12), show="*")
        self.pin_entry.pack(side=tk.LEFT, padx=10)
        
        # Login button
        login_btn = tk.Button(self.root, text="Login", font=('Arial', 14), 
                             bg='#3498DB', fg='white', width=15, command=self.login)
        login_btn.pack(pady=20)
        
        # Focus on account entry
        self.acc_entry.focus()
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
    
    def login(self):
        """Authenticate user"""
        account_number = self.acc_entry.get()
        pin = self.pin_entry.get()
        
        if not account_number or not pin:
            messagebox.showerror("Error", "Please enter both account number and PIN")
            return
        
        self.cursor.execute(
            "SELECT * FROM accounts WHERE account_number = ? AND pin = ?", 
            (account_number, pin)
        )
        account = self.cursor.fetchone()
        
        if account:
            self.current_user = account[3]  # name
            self.current_account = account[0]  # account number
            self.create_main_menu()
        else:
            messagebox.showerror("Error", "Invalid account number or PIN")
            self.pin_entry.delete(0, tk.END)
            self.pin_entry.focus()
    
    def create_main_menu(self):
        """Create the main menu after login"""
        self.clear_screen()
        
        # Welcome message
        welcome_label = tk.Label(self.root, text=f"Welcome, {self.current_user}", 
                                font=('Arial', 16, 'bold'), bg='#2C3E50', fg='#ECF0F1')
        welcome_label.pack(pady=20)
        
        # Menu buttons
        button_style = {'font': ('Arial', 12), 'bg': '#3498DB', 'fg': 'white', 
                       'width': 20, 'height': 2}
        
        balance_btn = tk.Button(self.root, text="Balance Inquiry", 
                               command=self.balance_inquiry, **button_style)
        balance_btn.pack(pady=10)
        
        withdraw_btn = tk.Button(self.root, text="Cash Withdrawal", 
                                command=self.withdraw_menu, **button_style)
        withdraw_btn.pack(pady=10)
        
        deposit_btn = tk.Button(self.root, text="Deposit Money", 
                               command=self.deposit_menu, **button_style)
        deposit_btn.pack(pady=10)
        
        pin_change_btn = tk.Button(self.root, text="Change PIN", 
                                  command=self.change_pin, **button_style)
        pin_change_btn.pack(pady=10)
        
        history_btn = tk.Button(self.root, text="Transaction History", 
                               command=self.transaction_history, **button_style)
        history_btn.pack(pady=10)
        
        logout_btn = tk.Button(self.root, text="Logout", 
                              command=self.logout, bg='#E74C3C', fg='white',
                              font=('Arial', 12), width=20, height=2)
        logout_btn.pack(pady=10)
    
    def balance_inquiry(self):
        """Display current balance"""
        self.cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?", 
            (self.current_account,)
        )
        balance = self.cursor.fetchone()[0]
        
        messagebox.showinfo("Balance Inquiry", 
                           f"Your current balance is: ${balance:.2f}")
    
    def withdraw_menu(self):
        """Create withdrawal menu"""
        self.clear_screen()
        
        title_label = tk.Label(self.root, text="Cash Withdrawal", 
                              font=('Arial', 16, 'bold'), bg='#2C3E50', fg='#ECF0F1')
        title_label.pack(pady=20)
        
        # Quick withdrawal buttons
        amounts = [20, 40, 60, 80, 100, 200, 300]
        for amount in amounts:
            btn = tk.Button(self.root, text=f"${amount}", 
                           font=('Arial', 12), bg='#3498DB', fg='white',
                           width=15, command=lambda amt=amount: self.withdraw(amt))
            btn.pack(pady=5)
        
        # Custom amount button
        custom_btn = tk.Button(self.root, text="Other Amount", 
                              font=('Arial', 12), bg='#F39C12', fg='white',
                              width=15, command=self.withdraw_custom)
        custom_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.root, text="Back to Menu", 
                            font=('Arial', 12), bg='#95A5A6', fg='white',
                            width=15, command=self.create_main_menu)
        back_btn.pack(pady=10)
    
    def withdraw(self, amount):
        """Process withdrawal"""
        self.cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?", 
            (self.current_account,)
        )
        balance = self.cursor.fetchone()[0]
        
        if amount > balance:
            messagebox.showerror("Error", "Insufficient funds")
            return
        
        if amount <= 0:
            messagebox.showerror("Error", "Invalid amount")
            return
        
        # Update balance
        new_balance = balance - amount
        self.cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_number = ?", 
            (new_balance, self.current_account)
        )
        
        # Record transaction
        self.record_transaction('WITHDRAWAL', amount)
        
        self.conn.commit()
        
        messagebox.showinfo("Success", 
                           f"${amount:.2f} withdrawn successfully.\nNew balance: ${new_balance:.2f}")
        self.create_main_menu()
    
    def withdraw_custom(self):
        """Withdraw custom amount"""
        amount = simpledialog.askfloat("Custom Withdrawal", "Enter amount to withdraw:")
        if amount is not None:
            self.withdraw(amount)
    
    def deposit_menu(self):
        """Create deposit menu"""
        self.clear_screen()
        
        title_label = tk.Label(self.root, text="Deposit Money", 
                              font=('Arial', 16, 'bold'), bg='#2C3E50', fg='#ECF0F1')
        title_label.pack(pady=20)
        
        # Deposit amount entry
        amount_frame = tk.Frame(self.root, bg='#2C3E50')
        amount_frame.pack(pady=10)
        tk.Label(amount_frame, text="Amount: $", font=('Arial', 12), 
                bg='#2C3E50', fg='#ECF0F1').pack(side=tk.LEFT)
        self.deposit_entry = tk.Entry(amount_frame, font=('Arial', 12))
        self.deposit_entry.pack(side=tk.LEFT, padx=10)
        
        # Deposit button
        deposit_btn = tk.Button(self.root, text="Deposit", 
                               font=('Arial', 12), bg='#3498DB', fg='white',
                               width=15, command=self.process_deposit)
        deposit_btn.pack(pady=10)
        
        # Back button
        back_btn = tk.Button(self.root, text="Back to Menu", 
                            font=('Arial', 12), bg='#95A5A6', fg='white',
                            width=15, command=self.create_main_menu)
        back_btn.pack(pady=10)
        
        self.deposit_entry.focus()
    
    def process_deposit(self):
        """Process deposit"""
        try:
            amount = float(self.deposit_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            return
        
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be positive")
            return
        
        # Update balance
        self.cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?", 
            (self.current_account,)
        )
        balance = self.cursor.fetchone()[0]
        new_balance = balance + amount
        
        self.cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_number = ?", 
            (new_balance, self.current_account)
        )
        
        # Record transaction
        self.record_transaction('DEPOSIT', amount)
        
        self.conn.commit()
        
        messagebox.showinfo("Success", 
                           f"${amount:.2f} deposited successfully.\nNew balance: ${new_balance:.2f}")
        self.create_main_menu()
    
    def change_pin(self):
        """Change PIN functionality"""
        current_pin = simpledialog.askstring("Change PIN", "Enter current PIN:", show='*')
        if not current_pin:
            return
        
        # Verify current PIN
        self.cursor.execute(
            "SELECT pin FROM accounts WHERE account_number = ?", 
            (self.current_account,)
        )
        actual_pin = self.cursor.fetchone()[0]
        
        if current_pin != actual_pin:
            messagebox.showerror("Error", "Incorrect current PIN")
            return
        
        new_pin = simpledialog.askstring("Change PIN", "Enter new PIN:", show='*')
        if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
            messagebox.showerror("Error", "PIN must be 4 digits")
            return
        
        confirm_pin = simpledialog.askstring("Change PIN", "Confirm new PIN:", show='*')
        if new_pin != confirm_pin:
            messagebox.showerror("Error", "PINs do not match")
            return
        
        # Update PIN
        self.cursor.execute(
            "UPDATE accounts SET pin = ? WHERE account_number = ?", 
            (new_pin, self.current_account)
        )
        self.conn.commit()
        
        messagebox.showinfo("Success", "PIN changed successfully")
    
    def transaction_history(self):
        """Display transaction history"""
        self.cursor.execute(
            "SELECT type, amount, timestamp FROM transactions WHERE account_number = ? ORDER BY timestamp DESC LIMIT 10", 
            (self.current_account,)
        )
        transactions = self.cursor.fetchall()
        
        if not transactions:
            messagebox.showinfo("Transaction History", "No transactions found")
            return
        
        history_text = "Last 10 Transactions:\n\n"
        for trans in transactions:
            history_text += f"{trans[2]}: {trans[0]} - ${trans[1]:.2f}\n"
        
        messagebox.showinfo("Transaction History", history_text)
    
    def record_transaction(self, trans_type, amount):
        """Record a transaction in the database"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            "INSERT INTO transactions (account_number, type, amount, timestamp) VALUES (?, ?, ?, ?)",
            (self.current_account, trans_type, amount, timestamp)
        )
    
    def logout(self):
        """Logout and return to login screen"""
        self.current_user = None
        self.current_account = None
        self.create_login_screen()
    
    def clear_screen(self):
        """Clear all widgets from the screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'conn'):
            self.conn.close()

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ATMInterface(root)
    root.mainloop()