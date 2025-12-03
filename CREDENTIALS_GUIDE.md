# MongoDB Credentials Management Guide

## Overview

This system now fetches MT5 credentials dynamically from MongoDB instead of using hardcoded arrays. This provides better security, flexibility, and centralized management.

## 📁 MongoDB Structure

### Database & Collections

- **Database**: `test` (configurable in `config.py`)
- **Credentials Collection**: `credentialkeys`
- **Reports Collection**: `credentials_reports`

### Credential Document Schema

```javascript
{
  "_id": ObjectId("..."),
  "key": "2K_1STEP",  // Credential group identifier
  "credentials": [
    {
      "loginId": "279016303",        // MT5 account number
      "password": "adA8921#",        // MT5 password
      "isActive": true,              // Only true credentials are processed
      "assignedTo": "User Name (email@example.com)",  // Optional
      "assignedOrderId": "order_123",                 // Optional
      "assignedAt": ISODate("2025-08-02T09:07:49.915Z"), // Optional
      "isBreached": false,           // Optional breach tracking
      "lastChecked": ISODate("..."), // Optional last check date
      "breachedMetadata": ""         // Optional breach details
    }
  ],
  "createdAt": ISODate("..."),
  "updatedAt": ISODate("...")
}
```

## 🔑 Key Fields

### Required Fields

- `loginId` (string): MT5 account login number
- `password` (string): MT5 account password
- `isActive` (boolean): Controls whether this credential is processed

### Optional Fields

- `assignedTo` (string): Who is using this account
- `assignedOrderId` (string): Related order/transaction ID
- `assignedAt` (Date): When it was assigned
- `isBreached` (boolean): Flag for compromised accounts
- `lastChecked` (Date): Last verification date
- `breachedMetadata` (string): Details about breach/issues

## 🚀 Quick Start

### 1. View Your Credentials

```bash
# See all credentials
python view_credentials.py

# See only active credentials
python view_credentials.py --active-only
```

### 2. Run the Automation

```bash
python main.py
```

The automation will:

1. Connect to MongoDB
2. Fetch all credentials from `credentialkeys` collection
3. Filter for credentials where:
   - `isActive: true` AND
   - `isBreached` is NOT `true` (if field is missing or `false`, credential is considered safe)
4. Process each eligible account
5. Save reports to `credentials_reports` collection
6. **Auto-update credential status**:
   - Set `lastChecked` to current timestamp
   - Set `isBreached` to `false`
   - Set `breachedMetadata` to "will be known soon"

## 📝 Managing Credentials

### Adding New Credentials

Add credentials directly to MongoDB using MongoDB Compass, mongosh, or your application:

```javascript
db.credentialkeys.insertOne({
  key: "NEW_GROUP",
  credentials: [
    {
      loginId: "123456789",
      password: "YourPassword123!",
      isActive: true,
    },
  ],
  createdAt: new Date(),
  updatedAt: new Date(),
});
```

### Enabling/Disabling Credentials

Toggle the `isActive` flag:

```javascript
// Disable a credential
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { $set: { "credentials.$.isActive": false } }
);

// Enable a credential
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { $set: { "credentials.$.isActive": true } }
);
```

### Assigning Credentials

```javascript
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  {
    $set: {
      "credentials.$.assignedTo": "John Doe (john@example.com)",
      "credentials.$.assignedOrderId": "order_12345",
      "credentials.$.assignedAt": new Date(),
    },
  }
);
```

### Marking as Breached

```javascript
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  {
    $set: {
      "credentials.$.isBreached": true,
      "credentials.$.breachedMetadata":
        "Account locked due to suspicious activity",
      "credentials.$.isActive": false, // Disable breached accounts
      "credentials.$.lastChecked": new Date(),
    },
  }
);
```

## 🔍 Querying Credentials

### Find All Active Credentials

```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { $match: { "credentials.isActive": true } },
  {
    $project: {
      key: 1,
      loginId: "$credentials.loginId",
      assignedTo: "$credentials.assignedTo",
    },
  },
]);
```

### Find Unassigned Active Credentials

```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  {
    $match: {
      "credentials.isActive": true,
      "credentials.assignedTo": { $exists: false },
    },
  },
  {
    $project: {
      key: 1,
      loginId: "$credentials.loginId",
    },
  },
]);
```

### Count Credentials by Status

```javascript
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  {
    $group: {
      _id: "$credentials.isActive",
      count: { $sum: 1 },
    },
  },
]);
```

## 🛠️ Configuration

Edit `config.py`:

```python
# MongoDB Settings
MONGODB_URI = 'mongodb://localhost:27017/'  # Or MongoDB Atlas URI
MONGODB_DATABASE = 'test'

# MT5 Server (applies to all credentials)
SERVER = "Exness-MT5Trial8"
```

## 🔄 Automatic Credential Updates

After successfully processing each account, the system automatically updates the credential status:

```javascript
{
  "lastChecked": ISODate("2025-11-30T10:30:00.000Z"),  // Current timestamp
  "isBreached": false,                                  // Hardcoded to false
  "breachedMetadata": "will be known soon",            // Default message
  "updatedAt": ISODate("2025-11-30T10:30:00.000Z")     // Document update time
}
```

This helps you track:
- ✅ When each credential was last verified
- ✅ Which accounts are currently working
- ✅ Breach status (for future implementation)

## ⚠️ Important Notes

1. **Security**: Store MongoDB credentials securely using environment variables
2. **Active Flag**: Only credentials with `isActive: true` are processed
3. **Breach Protection**: 
   - Credentials are skipped ONLY if `isBreached: true`
   - If `isBreached` field is missing or `false`, credential is considered safe
   - By default, credentials without the `isBreached` field are NOT breached
4. **Server Name**: The `SERVER` in `config.py` applies to all fetched credentials
5. **Batch Processing**: Credentials are processed sequentially with delays
6. **Error Handling**: Failed accounts don't stop the pipeline
7. **Auto-Updates**: Credentials are automatically updated after successful processing

## 🔒 Security Best Practices

1. **Environment Variables**: Use `.env` file for MongoDB connection strings
2. **Access Control**: Limit MongoDB access to authorized users only
3. **Encryption**: Use MongoDB encryption at rest and in transit
4. **Audit Logging**: Track who modifies credentials and when
5. **Regular Reviews**: Periodically review and disable unused credentials

## 📊 Monitoring

### Check Last Run Results

```javascript
// Get accounts processed in last run
db.credentials_reports.find().sort({ updatedAt: -1 }).limit(10);
```

### Find Accounts Not Updated Recently

```javascript
// Accounts not updated in last 7 days
db.credentials_reports.find({
  updatedAt: {
    $lt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  },
});
```

## 🆘 Troubleshooting

### No Credentials Found

```bash
# Check if credentials exist
python view_credentials.py

# Verify MongoDB connection
python mongo_db.py
```

### Credentials Not Processing

1. Verify `isActive: true`
2. Check MongoDB connection in `config.py`
3. Ensure collection name is correct: `credentialkeys`
4. Check server name matches in `config.py`

### Connection Issues

1. Verify `MONGODB_URI` in `config.py`
2. Check MongoDB is running
3. Test connection: `python mongo_db.py`
4. Check firewall/network settings

## 📚 Related Files

- `config.py` - Configuration settings
- `mongo_db.py` - MongoDB operations
- `main.py` - Main automation pipeline
- `view_credentials.py` - Credential viewer utility
