# 🚀 Quick Start Guide

## 30 Second Setup

### 1. Install (Windows)

```bash
install.bat
```

Or manually:

```bash
pip install -r requirements.txt
copy config.example.py config.py
```

### 2. Configure

Edit `config.py`:

```python
ACCOUNTS = [
    {
        "login": YOUR_ACCOUNT_NUMBER,
        "password": "YOUR_PASSWORD",
        "server": "YOUR_BROKER_SERVER"
    }
]
```

### 3. Run

```bash
python main.py
```

## MongoDB Setup

### Local (Easiest)

1. Install MongoDB Community: https://www.mongodb.com/try/download/community
2. Start MongoDB (usually automatic)
3. Done! (Uses `mongodb://localhost:27017/` by default)

### Cloud (Free Tier)

1. Create account: https://www.mongodb.com/cloud/atlas/register
2. Create free M0 cluster
3. Get connection string
4. Update in `config.py`:
   ```python
   MONGODB_URI = 'mongodb+srv://user:pass@cluster.mongodb.net/'
   ```

## File Overview

| File                | Purpose                                |
| ------------------- | -------------------------------------- |
| `main.py`           | Run this to process all accounts       |
| `config.py`         | Your accounts and settings (EDIT THIS) |
| `automation.py`     | MT5 automation logic                   |
| `parse.py`          | Report parser                          |
| `mongo_db.py`       | MongoDB integration                    |
| `query_accounts.py` | View MongoDB data                      |

## Common Commands

```bash
# Process all accounts
python main.py

# Query MongoDB data
python query_accounts.py

# Test MongoDB connection
python mongo_db.py

# Test automation (single account)
python automation.py

# Parse existing report
python parse.py path/to/report.html
```

## What Gets Stored in MongoDB?

✅ Account details (name, broker, number)  
✅ Balance and equity history  
✅ Growth and drawdown metrics  
✅ Profit/loss analysis  
✅ Long/Short performance  
✅ Symbol statistics  
✅ Risk indicators  
✅ Complete trading history

## Troubleshooting

| Issue                     | Solution                              |
| ------------------------- | ------------------------------------- |
| MongoDB connection failed | Check MongoDB is running, verify URI  |
| MT5 automation failed     | Close MT5, check paths in config.py   |
| Module not found          | Run `pip install -r requirements.txt` |
| Account processing failed | Check credentials in config.py        |

## Next Steps

1. ✅ Run `python main.py` to process accounts
2. ✅ Check MongoDB with `python query_accounts.py`
3. ✅ View data in MongoDB Compass (download: https://www.mongodb.com/products/compass)
4. ✅ Schedule regular runs (Task Scheduler/cron)
5. ✅ Build your dashboard!

## Need Help?

- 📖 Full Documentation: `README.md`
- 🛠️ Setup Guide: `SETUP_GUIDE.md`
- 📊 Implementation Details: `IMPLEMENTATION_SUMMARY.md`

## Example Output

```
================================================================================
🏁 MT5 Multi-Account Automation + MongoDB Pipeline
================================================================================

📊 Total accounts to process: 2
✅ Connected to MongoDB: mt5_trading

================================================================================
Processing account 1/2
================================================================================
🔄 Processing Account: 123456789
🚀 Launching MT5...
🔐 Logging into MT5 with account 123456789...
✅ Login complete.
📄 Generating report...
💾 Saving report...
✅ Report saved
✅ Report parsing complete
✅ Data saved to MongoDB
✅ Account 123456789 processed successfully!

📊 PROCESSING SUMMARY
================================================================================
✅ Successfully processed: 2 accounts
   Accounts: 123456789, 987654321

🎉 Pipeline finished!
```

---

**That's it! You're ready to automate your MT5 reporting! 🚀**
