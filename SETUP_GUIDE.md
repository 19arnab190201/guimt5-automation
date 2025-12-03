# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Your Accounts

Edit `config.py` and add your MT5 accounts:

```python
ACCOUNTS = [
    {
        "login": 123456789,
        "password": "your_password",
        "server": "YourBroker-Server"
    },
    {
        "login": 987654321,
        "password": "another_password",
        "server": "AnotherBroker-Server"
    },
]
```

## Step 3: Setup MongoDB

### Option A: Local MongoDB (Recommended for Testing)

1. Download and install [MongoDB Community Edition](https://www.mongodb.com/try/download/community)
2. Start MongoDB:
   - Windows: MongoDB should start automatically as a service
   - Or manually: `mongod` command
3. Keep default settings in `config.py`:
   ```python
   MONGODB_URI = 'mongodb://localhost:27017/'
   ```

### Option B: MongoDB Atlas (Cloud - Free Tier Available)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a free cluster (M0 Sandbox)
3. Create a database user (Database Access)
4. Whitelist your IP address (Network Access → Add IP Address → Allow Access from Anywhere for testing)
5. Get your connection string:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string
6. Update `config.py`:
   ```python
   MONGODB_URI = 'mongodb+srv://username:password@cluster.mongodb.net/'
   ```

## Step 4: Verify MT5 Installation Path

Check if MT5 is installed at the default location in `config.py`:

```python
MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
```

If your MT5 is installed elsewhere, update the path.

## Step 5: Run the Automation

```bash
python main.py
```

## What Happens Next?

The script will:

1. ✅ Connect to MongoDB
2. ✅ Process each account sequentially:
   - Launch MT5
   - Login with credentials
   - Generate report
   - Parse the HTML report
   - Save to MongoDB
   - Save JSON file locally (optional)
3. ✅ Display a summary of results

## Troubleshooting

### "MongoDB connection failed"

- Verify MongoDB is running (local) or check your Atlas connection string
- For Atlas: Check IP whitelist and database user credentials
- The script will continue and save data locally as JSON

### "MT5 automation failed"

- Ensure MT5 is closed before running
- Check MT5_PATH is correct
- Verify keyboard is set to English layout
- Try increasing delays in automation.py if your PC is slower

### "Report not found"

- Check DOWNLOAD_FOLDER path in config.py
- Ensure you have write permissions to the folder
- Check if MT5 report generation worked manually first

## Testing Individual Components

Test MongoDB connection:

```bash
python mongo_db.py
```

Test automation for single account:

```bash
python automation.py
```

Parse an existing report:

```bash
python parse.py path/to/report.html
```

## Configuration Options

In `config.py`:

- `SAVE_JSON_FILES` - Save parsed data as JSON (True/False)
- `INTER_ACCOUNT_DELAY` - Seconds to wait between processing accounts
- `DOWNLOAD_FOLDER` - Where MT5 saves reports initially
- `REPORT_SAVE_PATH` - Where to organize/move reports

## Environment Variables (Alternative to config.py)

You can also use environment variables:

```bash
# Windows
set MONGODB_URI=mongodb://localhost:27017/
set MONGODB_DATABASE=mt5_trading

# Linux/Mac
export MONGODB_URI=mongodb://localhost:27017/
export MONGODB_DATABASE=mt5_trading
```

## Security Best Practices

1. **Never commit credentials**: Add `config.py` to `.gitignore` if using version control
2. **Use environment variables** for production
3. **Restrict MongoDB access** to specific IP addresses
4. **Use strong passwords** for MongoDB users
5. **Enable MongoDB authentication** in production

## Next Steps

Once setup is complete:

1. Verify data in MongoDB:

   - Use MongoDB Compass (GUI tool)
   - Or MongoDB Shell: `db.trading_accounts.find()`

2. Schedule regular runs:

   - Windows Task Scheduler
   - Linux: cron
   - Cloud: AWS Lambda, Azure Functions

3. Build a dashboard:
   - Connect to MongoDB from web app
   - Visualize trading performance
   - Real-time monitoring

## Need Help?

- Check the main `README.md` for detailed documentation
- Review error messages in console output
- Test components individually to isolate issues
