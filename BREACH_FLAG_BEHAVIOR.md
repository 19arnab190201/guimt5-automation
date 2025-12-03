# isBreached Flag Behavior

## 🔒 Default Behavior

**Important:** A credential is considered breached ONLY if the `isBreached` field is explicitly set to `true`.

## ✅ Processing Logic

### Credential WILL BE Processed:
```javascript
// Case 1: isBreached field doesn't exist
{
  "loginId": "279016303",
  "password": "password123",
  "isActive": true
  // No isBreached field = NOT breached ✅
}

// Case 2: isBreached is explicitly false
{
  "loginId": "279016303",
  "password": "password123",
  "isActive": true,
  "isBreached": false  // Explicitly NOT breached ✅
}

// Case 3: isBreached is null
{
  "loginId": "279016303",
  "password": "password123",
  "isActive": true,
  "isBreached": null  // Treated as NOT breached ✅
}
```

### Credential WILL BE Skipped:
```javascript
// Only this case - explicitly set to true
{
  "loginId": "279016303",
  "password": "password123",
  "isActive": true,
  "isBreached": true  // Explicitly breached ❌
}
```

## 🎯 Summary Table

| `isActive` | `isBreached` | Will Process? | Reason |
|------------|--------------|---------------|--------|
| `true` | Not present | ✅ Yes | Default = NOT breached |
| `true` | `false` | ✅ Yes | Explicitly safe |
| `true` | `null` | ✅ Yes | Treated as NOT breached |
| `true` | `true` | ❌ No | Explicitly breached |
| `false` | Not present | ❌ No | Not active |
| `false` | `false` | ❌ No | Not active |
| `false` | `true` | ❌ No | Not active + breached |

## 💻 Code Implementation

```python
# In mongo_db.py - get_active_credentials()
is_active = cred.get('isActive', False)
# Default to False if isBreached field doesn't exist
# Only considered breached if explicitly set to True
is_breached = cred.get('isBreached', False)

# Only process if active AND not breached
if is_active and not is_breached:
    # Process this credential
```

## 🔍 How to Check

### Query All Safe Credentials
```javascript
// All credentials that WILL be processed
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { 
    $match: { 
      "credentials.isActive": true,
      $or: [
        { "credentials.isBreached": { $ne: true } },
        { "credentials.isBreached": { $exists: false } }
      ]
    } 
  }
])
```

### Query Only Breached Credentials
```javascript
// All credentials that will be SKIPPED due to breach
db.credentialkeys.aggregate([
  { $unwind: "$credentials" },
  { $match: { "credentials.isBreached": true } }
])
```

## 🛡️ Security Implications

### Why This Default?

1. **Backwards Compatible**: Old credentials without the field still work
2. **Explicit Flagging**: Only mark as breached when you KNOW it's compromised
3. **Safe by Default**: New credentials are assumed safe unless proven otherwise
4. **Clear Intent**: `isBreached: true` is an explicit security flag

### Best Practices

1. **Add the field**: Always include `isBreached: false` when creating new credentials
2. **Monitor actively**: Check credentials regularly and update the flag if compromised
3. **Use metadata**: When setting `isBreached: true`, always add `breachedMetadata` with details
4. **Track timing**: Update `lastChecked` to know when the credential was last verified

## 📝 Example Workflow

### Creating a New Credential
```javascript
db.credentialkeys.updateOne(
  { key: "2K_1STEP" },
  {
    $push: {
      credentials: {
        loginId: "279016350",
        password: "SecurePass123!",
        isActive: true,
        isBreached: false,  // Explicitly set to false
        createdAt: new Date()
      }
    }
  }
)
```

### Marking a Credential as Breached
```javascript
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { 
    $set: { 
      "credentials.$.isBreached": true,  // Explicitly flag as breached
      "credentials.$.breachedMetadata": "Account locked by broker",
      "credentials.$.isActive": false,  // Also deactivate it
      "credentials.$.lastChecked": new Date()
    }
  }
)
```

### Unmarking a Credential (After Issue Resolved)
```javascript
db.credentialkeys.updateOne(
  { key: "2K_1STEP", "credentials.loginId": "279016303" },
  { 
    $set: { 
      "credentials.$.isBreached": false,  // Mark as safe again
      "credentials.$.breachedMetadata": "Issue resolved - account unlocked",
      "credentials.$.isActive": true,  // Reactivate it
      "credentials.$.lastChecked": new Date()
    }
  }
)
```

## ⚠️ Important Notes

1. **Field is optional**: System works with or without the `isBreached` field
2. **Explicit flagging only**: Only `isBreached: true` will skip processing
3. **Safe defaults**: Missing, `false`, `null` = credential is safe
4. **Automatic updates**: System sets `isBreached: false` after successful processing
5. **Manual override**: You can manually set `isBreached: true` to block a credential

