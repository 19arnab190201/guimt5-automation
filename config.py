"""
Configuration file for MT5 Multi-Account Automation
Edit this file to configure your accounts and MongoDB settings
"""
import os

# ================= ACCOUNTS CONFIGURATION =================
# NOTE: Accounts are now fetched dynamically from MongoDB!
# The automation will fetch active credentials from the 'credentialkeys' collection
# Only credentials with 'isActive: true' will be processed

SERVER = "Exness-MT5Trial8"

# Legacy hardcoded accounts (NOT USED - kept for reference only)
# Credentials are now managed in MongoDB collection: credentialkeys
ACCOUNTS = [
    # Example format (for reference only - not used by automation):
    # {
    #     "login": 279331520,
    #     "password": "Hindi@1234",
    #     "server": SERVER
    # },
]

# ================= MONGODB CONFIGURATION =================
# MongoDB Connection String
# Local MongoDB: mongodb://localhost:27017/
# MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://arnabdkumar_db_user:vbaNFD274Xa3ltYK@prop-test.h0du9br.mongodb.net/')

# MongoDB Database Name
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'test')

# ================= MT5 CONFIGURATION =================
# Path to MetaTrader 5 executable
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

# Folder where MT5 saves reports initially
# DOWNLOAD_FOLDER = r"C:\Users\arnab\Desktop\report_automation"
DOWNLOAD_FOLDER = r"C:\Users\Administrator\Desktop\report_automation"
# Folder to organize saved reports
# REPORT_SAVE_PATH = r"C:\Users\arnab\Desktop\report_automation"
REPORT_SAVE_PATH = r"C:\Users\Administrator\Desktop\report_automation"
# C:\Users\Administrator\Desktop\report_automation

# ================= OTHER SETTINGS =================
# Save parsed data as JSON files locally
SAVE_JSON_FILES = True

# Delay between processing accounts (seconds)
INTER_ACCOUNT_DELAY = 5

# Enable verbose logging
VERBOSE = True

