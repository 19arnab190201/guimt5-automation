"""
Configuration file for MT5 Multi-Account Automation
COPY THIS FILE TO config.py AND EDIT WITH YOUR ACTUAL CREDENTIALS

cp config.example.py config.py   (Linux/Mac)
copy config.example.py config.py (Windows)
"""
import os

# ================= ACCOUNTS CONFIGURATION =================
# Add all your MT5 accounts here
# Each account needs: login, password, and server

ACCOUNTS = [
    {
        "login": 123456789,              # Your MT5 account number
        "password": "your_password",     # Your MT5 password
        "server": "YourBroker-Server"    # Your broker server name
    },
    # Add more accounts below:
    # {
    #     "login": 987654321,
    #     "password": "another_password",
    #     "server": "Another-Server-Name"
    # },
]

# ================= MONGODB CONFIGURATION =================
# MongoDB Connection String
# Local MongoDB: mongodb://localhost:27017/
# MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

# MongoDB Database Name
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'mt5_trading')

# ================= MT5 CONFIGURATION =================
# Path to MetaTrader 5 executable
# Update this if your MT5 is installed in a different location
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# Folder where MT5 saves reports initially (usually Desktop or Downloads)
DOWNLOAD_FOLDER = r"C:\Users\YOUR_USERNAME\Desktop"

# Folder to organize and store saved reports
REPORT_SAVE_PATH = r"C:\MT5_Reports"

# ================= OTHER SETTINGS =================
# Save parsed data as JSON files locally (in addition to MongoDB)
SAVE_JSON_FILES = True

# Delay between processing accounts (seconds)
# Increase if you experience issues with MT5 not closing/opening properly
INTER_ACCOUNT_DELAY = 5

# Enable verbose logging
VERBOSE = True

