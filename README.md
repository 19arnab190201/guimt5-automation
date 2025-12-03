# MT5 Multi-Account Automation with MongoDB Integration

Automated MetaTrader 5 report generation, parsing, and MongoDB storage system for multiple trading accounts.

## 🚀 Features

- **Dynamic Credential Management**: Fetch credentials from MongoDB - no hardcoded passwords
- **Multi-Account Support**: Process multiple MT5 accounts in a single run
- **Automated Report Generation**: Automatically logs into MT5, generates reports, and saves them
- **Data Parsing**: Extracts comprehensive trading data from HTML reports
- **MongoDB Integration**: Stores parsed data in MongoDB with a well-structured schema
- **Active/Inactive Control**: Enable/disable accounts dynamically via database
- **Credential Tracking**: Track who accounts are assigned to and when
- **Local JSON Backup**: Optionally saves parsed data as JSON files
- **Error Handling**: Robust error handling with detailed logging
- **Credential Viewer**: Built-in tool to view and verify credentials

## 📋 Prerequisites

- **Windows OS** (for pyautogui automation)
- **MetaTrader 5** installed at: `C:\Program Files\MetaTrader 5\terminal64.exe`
- **Python 3.8+**
- **MongoDB** (local or cloud instance like MongoDB Atlas)

## 🛠️ Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up MongoDB:**

   - **Option A - Local MongoDB:**

     - Install MongoDB Community Edition
     - Start MongoDB service
     - Default connection: `mongodb://localhost:27017/`

   - **Option B - MongoDB Atlas (Cloud):**
     - Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
     - Create a cluster and get your connection string
     - Update the connection string in your `.env` file

4. **Configure MongoDB connection (optional):**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your MongoDB credentials if not using localhost.

## ⚙️ Configuration

### Managing Credentials via MongoDB

**🎉 NEW**: Credentials are now managed dynamically through MongoDB!

The system fetches active credentials from the `credentialkeys` collection in MongoDB. This allows you to:

- ✅ Manage credentials centrally in your database
- ✅ Enable/disable accounts without changing code
- ✅ Track credential assignments and usage
- ✅ Add/remove accounts dynamically

**Credential Document Structure:**

```javascript
{
  "key": "2K_1STEP",
  "credentials": [
    {
      "loginId": "279016303",
      "password": "adA8921#",
      "isActive": true,
      "assignedTo": "User Name (email@example.com)",
      "assignedOrderId": "order_id_123",
      "assignedAt": ISODate("2025-08-02T09:07:49.915Z")
    }
  ]
}
```

**View Your Credentials:**

```bash
# View all credentials (active and inactive)
python view_credentials.py

# View only active credentials that will be processed
python view_credentials.py --active-only
```

**Important:** Only credentials with `isActive: true` are processed. Credentials are skipped ONLY if `isBreached` is explicitly set to `true`. If the `isBreached` field is missing, the credential is considered safe.

### MongoDB Configuration

Configure your MongoDB connection in `config.py`:

```python
MONGODB_URI = 'mongodb://localhost:27017/'  # Or your MongoDB Atlas URI
MONGODB_DATABASE = 'test'
SERVER = "Exness-MT5Trial8"  # Your MT5 server name
```

### Other Settings

- `SAVE_JSON_FILES = True` - Save parsed data as JSON files locally
- `MT5_PATH` in `automation.py` - Path to MT5 executable
- `DOWNLOAD_FOLDER` in `automation.py` - Where reports are initially saved

## 🎯 Usage

### Step 1: View Your Credentials

First, verify your credentials are properly configured in MongoDB:

```bash
python view_credentials.py
```

This will show all credentials and highlight which ones are active and will be processed.

### Step 2: Run the Complete Pipeline

Process all active accounts:

```bash
python main.py
```

This will:

1. **Fetch** all active credentials from MongoDB
2. **Process** each account sequentially
3. **Generate** MT5 reports automatically
4. **Parse** the HTML reports
5. **Save** data to MongoDB (`credentials_reports` collection)
6. **Update** credential status (lastChecked, isBreached, breachedMetadata)
7. **Export** JSON files locally (optional)
8. **Display** a summary of results

### Test Individual Components:

**Test single account automation:**

```bash
python automation.py
```

**Parse an existing report:**

```bash
python parse.py path/to/report.html
```

**Test MongoDB connection:**

```bash
python mongo_db.py
```

**View credentials:**

```bash
# All credentials
python view_credentials.py

# Active only
python view_credentials.py --active-only
```

## 📊 MongoDB Schema

The system stores trading data in a comprehensive schema with the following main sections:

- **Account Information**: Name, broker, account number, currency, type
- **Summary Metrics**: Gain, activity, deposits, withdrawals
- **Balance & Equity**: Historical balance and equity data
- **Growth & Drawdown**: Performance metrics over time
- **Profit Analysis**: Total, daily, by type (robot/manual/signals)
- **Long/Short Performance**: Trade statistics and indicators
- **Symbol Analysis**: Performance by trading symbols
- **Risk Metrics**: Drawdown, MFE/MAE, risk indicators

### Key Collections

- **`credentials_reports`** - Stores parsed trading report data for all accounts
- **`credentialkeys`** - Manages MT5 login credentials with active/inactive status

### Indexes

The schema includes indexes on:

- `account` (unique) - Account number for quick lookups
- `broker` - Filter by broker
- `type` - Filter by account type (demo/real)
- `createdAt`

## 📁 Project Structure

```
├── main.py              # Main orchestration script for multiple accounts
├── automation.py        # MT5 automation using pyautogui
├── parse.py            # HTML report parser
├── mongo_db.py         # MongoDB integration and data transformation
├── requirements.txt    # Python dependencies
├── .env.example        # Environment configuration template
└── README.md           # This file
```

## 🔧 How It Works

### 1. Automation (`automation.py`)

- Launches MT5 terminal
- Logs into specified account
- Generates report via keyboard shortcuts
- Saves report to disk

### 2. Parsing (`parse.py`)

- Reads HTML report file
- Extracts JSON data from `window.__report` object
- Displays key metrics and timeline data

### 3. MongoDB Integration (`mongo_db.py`)

- Connects to MongoDB
- Transforms parsed data to match schema
- Upserts data (insert or update) based on account number
- Handles duplicate accounts gracefully

### 4. Multi-Account Orchestration (`main.py`)

- Iterates through account list
- Processes each account with error handling
- Collects results and displays summary
- Manages MongoDB connection lifecycle

## ⚠️ Important Notes

1. **Screen Resolution**: The automation uses screen coordinates. Ensure MT5 windows appear consistently.

2. **Timing**: The script includes delays for UI interactions. Adjust if your system is slower/faster.

3. **Failsafe**: pyautogui's failsafe is enabled - move mouse to screen corner to abort.

4. **MT5 Installation Path**: Update `MT5_PATH` in `automation.py` if your installation differs.

5. **Data Privacy**: Be cautious with credentials. Consider using environment variables for sensitive data.

6. **MongoDB Connection**: The system continues to run even if MongoDB connection fails, saving data locally only.

## 🐛 Troubleshooting

### MongoDB Connection Issues

```python
# Test your connection
python mongo_db.py
```

- Verify MongoDB is running
- Check firewall settings
- Verify connection string format
- For Atlas: Check IP whitelist and database user permissions

### Automation Issues

- Ensure MT5 is not already running
- Check if keyboard language is set to English
- Verify MT5 installation path
- Adjust timing delays if automation is too fast

### Parsing Issues

- Ensure report HTML file exists
- Verify file encoding (UTF-8)
- Check if report format has changed

## 📈 Future Enhancements

- [ ] Support for concurrent account processing
- [ ] Web dashboard for data visualization
- [ ] Email notifications on completion/errors
- [ ] Support for scheduled runs (cron/task scheduler)
- [ ] Additional data export formats (CSV, Excel)
- [ ] Real-time monitoring integration

## 📝 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Note**: This tool automates trading account analysis. Always verify data accuracy and use at your own risk.
