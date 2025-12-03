# MongoDB Structure Reference

## 📊 Database Structure

```
Database: test
├── credentialkeys           (Credentials management collection)
└── credentials_reports      (Trading reports collection)
```

## 🔑 Collections Overview

### 1. `credentialkeys` Collection

**Purpose**: Stores MT5 login credentials with active/inactive status management

**Document Structure**:
```javascript
{
  "_id": ObjectId("..."),
  "key": "2K_1STEP",                    // Credential group identifier
  "credentials": [                      // Array of credentials
    {
      "loginId": "279016303",           // MT5 account number (string)
      "password": "adA8921#",           // MT5 password (string)
      "isActive": true,                 // Processing flag (boolean)
      "assignedTo": "User Name (email)", // Optional: Assignment info
      "assignedOrderId": "order_id",    // Optional: Related order
      "assignedAt": ISODate("..."),     // Optional: Assignment date
      "isBreached": false,              // Optional: Security flag
      "lastChecked": ISODate("..."),    // Optional: Last check date
      "breachedMetadata": ""            // Optional: Breach details
    }
  ],
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

**Key Points**:
- Only credentials with `isActive: true` are processed
- Credentials are skipped ONLY if `isBreached: true` (explicitly set)
- **Default behavior**: Missing `isBreached` field = NOT breached (safe to process)
- The `loginId` field is a string (even though it's a number)
- Multiple credential groups can exist with different `key` values
- **Auto-updated fields**: After successful processing, `lastChecked`, `isBreached`, and `breachedMetadata` are automatically updated

### 2. `credentials_reports` Collection

**Purpose**: Stores parsed MT5 trading report data

**Document Structure**:
```javascript
{
  "_id": ObjectId("..."),
  "account": 279288123,                  // Account number (unique)
  "name": "PROPSCHOLAR DEMO 2",          // Account name
  "currency": "USD",                     // Account currency
  "type": "demo",                        // Account type (demo/real)
  "broker": "Exness Technologies Ltd",   // Broker name
  "digits": 2,                           // Price precision
  "summary": {                           // Summary metrics
    "gain": 0,
    "activity": 0,
    "deposit": [0, 0],
    "withdrawal": [0, 0],
    // ... more summary fields
  },
  "balance": {                           // Balance data
    "balance": 0,
    "equity": 0,
    // ... more balance fields
  },
  "growth": { ... },
  "dividend": { ... },
  "profitTotal": { ... },
  "profitMoney": { ... },
  "profitDeals": { ... },
  "profitDaily": { ... },
  "profitType": { ... },
  "longShortTotal": { ... },
  "longShort": { ... },
  "longShortDaily": { ... },
  "longShortIndicators": { ... },
  "tradeTypeTotal": { ... },
  "symbolMoney": { ... },
  "symbolDeals": { ... },
  "symbolIndicators": { ... },
  "symbolsTotal": { ... },
  "symbolTypes": { ... },
  "drawdown": { ... },
  "risksIndicators": { ... },
  "risksMfeMaePercent": { ... },
  "risksMfeMaeMoney": { ... },
  "summaryIndicators": { ... },
  "updatedAt": ISODate("...")            // Last update timestamp
}
```

**Key Points**:
- Account fields are at root level (flattened structure)
- `account` field is unique identifier
- Automatically updated with `updatedAt` timestamp

## 🔍 Common Queries

### Get All Active (Non-Breached) Credentials
```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { 
    $match: { 
      "credentials.isActive": true,
      $or: [
        { "credentials.isBreached": false },
        { "credentials.isBreached": { $exists: false } }
      ]
    } 
  },
  { $project: { 
    key: 1,
    loginId: "$credentials.loginId",
    assignedTo: "$credentials.assignedTo"
  }}
])
```

### Get All Reports
```javascript
db.credentials_reports.find().sort({ updatedAt: -1 })
```

### Find Report by Account Number
```javascript
db.credentials_reports.findOne({ account: 279288123 })
```

### Count Active vs Inactive Credentials
```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { $group: {
    _id: "$credentials.isActive",
    count: { $sum: 1 }
  }}
])
```

### View Recently Checked Credentials
```javascript
// Show credentials checked in last 24 hours
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { 
    $match: { 
      "credentials.lastChecked": { 
        $gte: new Date(Date.now() - 24 * 60 * 60 * 1000) 
      }
    }
  },
  {
    $project: {
      key: 1,
      loginId: "$credentials.loginId",
      lastChecked: "$credentials.lastChecked",
      isBreached: "$credentials.isBreached"
    }
  },
  { $sort: { lastChecked: -1 } }
])
```

### Find All Breached Credentials
```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { $match: { "credentials.isBreached": true } },
  {
    $project: {
      key: 1,
      loginId: "$credentials.loginId",
      breachedMetadata: "$credentials.breachedMetadata",
      lastChecked: "$credentials.lastChecked"
    }
  }
])
```

### Enable/Disable a Credential
```javascript
// Disable
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { $set: { "credentials.$.isActive": false } }
)

// Enable
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { $set: { "credentials.$.isActive": true } }
)
```

## 🚀 Workflow

1. **Credentials are stored** in `credentialkeys` collection
2. **Automation reads** active credentials where:
   - `isActive: true`
   - `isBreached` is NOT `true` (missing field or `false` = safe)
3. **Reports are generated** for each eligible credential
4. **Parsed data is saved** to `credentials_reports` collection
5. **Credential status is updated** automatically:
   - `lastChecked` = current timestamp
   - `isBreached` = false
   - `breachedMetadata` = "will be known soon"
6. **Reports are queryable** by account number or other fields

## 📝 Configuration

In `config.py`:
```python
MONGODB_URI = 'mongodb://localhost:27017/'
MONGODB_DATABASE = 'test'
SERVER = "Exness-MT5Trial8"
```

## 🛠️ Useful Commands

### View Credentials
```bash
python view_credentials.py
python view_credentials.py --active-only
```

### Test MongoDB Connection
```bash
python mongo_db.py
```

### Run Automation
```bash
python main.py
```

## 📌 Important Notes

1. **Database Name**: `test`
2. **Credentials Collection**: `credentialkeys` (NOT `test/credentialkeys`)
3. **Reports Collection**: `credentials_reports`
4. **Processing filters**: `isActive: true` AND `isBreached` is NOT `true`
5. **Breach defaults**: If `isBreached` field is missing, credential is considered safe (NOT breached)
6. **Breach protection**: Only explicitly breached credentials (`isBreached: true`) are skipped
7. **Account number is unique**: Used as primary identifier
8. **Server name applies to all**: Defined in `config.py`
9. **Auto-updates**: Credentials are automatically updated with `lastChecked` timestamp after each successful run

