"""
Helper script to view credentials from MongoDB
"""
from mongo_db import MT5MongoDB
import config

def view_all_credentials():
    """Display all credentials from MongoDB"""
    print("=" * 80)
    print("MT5 Credentials Viewer")
    print("=" * 80)
    
    try:
        # Connect to MongoDB
        mongo_db = MT5MongoDB(
            connection_string=config.MONGODB_URI, 
            database_name=config.MONGODB_DATABASE
        )
        
        # Get all credential documents
        print("\nFetching credentials from 'credentialkeys' collection...")
        credential_docs = list(mongo_db.credentials_collection.find())
        
        if not credential_docs:
            print("No credential documents found!")
            mongo_db.close()
            return
        
        print(f"Found {len(credential_docs)} credential document(s)\n")
        
        total_active = 0
        total_inactive = 0
        
        for doc in credential_docs:
            key = doc.get('key', 'Unknown')
            credentials = doc.get('credentials', [])
            
            print("=" * 80)
            print(f"Key: {key}")
            print(f"Total Credentials: {len(credentials)}")
            print("=" * 80)
            
            active_creds = [c for c in credentials if c.get('isActive', False)]
            inactive_creds = [c for c in credentials if not c.get('isActive', False)]
            breached_creds = [c for c in credentials if c.get('isBreached', False)]
            eligible_creds = [c for c in active_creds if not c.get('isBreached', False)]
            
            print(f"\nActive & Eligible Credentials ({len(eligible_creds)}):")
            if eligible_creds:
                for cred in eligible_creds:
                    print(f"  • Login: {cred['loginId']}")
                    print(f"    Password: {'*' * len(cred['password'])}")
                    if cred.get('assignedTo'):
                        print(f"    Assigned: {cred['assignedTo']}")
                    if cred.get('assignedOrderId'):
                        print(f"    Order ID: {cred['assignedOrderId']}")
                    if cred.get('lastChecked'):
                        print(f"    Last Checked: {cred['lastChecked']}")
                    print()
            else:
                print("  (No eligible credentials)\n")
            
            if breached_creds:
                print(f"Breached Credentials ({len(breached_creds)}) - Will NOT be processed:")
                for cred in breached_creds:
                    print(f"  • Login: {cred['loginId']}")
                    if cred.get('breachedMetadata'):
                        print(f"    Reason: {cred['breachedMetadata']}")
                    print()
            
            print(f"Inactive Credentials ({len(inactive_creds)}):")
            if inactive_creds:
                for cred in inactive_creds:
                    print(f"  • Login: {cred['loginId']}")
                    if cred.get('assignedTo'):
                        print(f"    Assigned: {cred['assignedTo']}")
                    print()
            else:
                print("  (No inactive credentials)\n")
            
            total_active += len(eligible_creds)
            total_inactive += len(inactive_creds)
        
        # Summary
        total_breached = sum(1 for doc in credential_docs for c in doc.get('credentials', []) if c.get('isBreached', False))
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Eligible Credentials (Active & Not Breached): {total_active}")
        print(f"Total Breached Credentials: {total_breached}")
        print(f"Total Inactive Credentials: {total_inactive}")
        print(f"Total Credentials: {total_active + total_inactive + total_breached}")
        print("=" * 80)
        
        # Show what will be processed
        print("\nCredentials that will be processed by automation:")
        print("Reports will be saved to collection: 'credentials_reports'")
        active_accounts = mongo_db.get_active_credentials(server_name=config.SERVER)
        if active_accounts:
            for i, account in enumerate(active_accounts, 1):
                print(f"  {i}. Login: {account['login']} | Key: {account['key']}")
                if account.get('assignedTo'):
                    print(f"     Assigned to: {account['assignedTo']}")
        else:
            print("  (None - no active credentials found)")
        
        mongo_db.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def view_active_only():
    """Display only active credentials"""
    print("=" * 80)
    print("Active MT5 Credentials")
    print("=" * 80)
    
    try:
        mongo_db = MT5MongoDB(
            connection_string=config.MONGODB_URI, 
            database_name=config.MONGODB_DATABASE
        )
        
        active_accounts = mongo_db.get_active_credentials(server_name=config.SERVER)
        
        if not active_accounts:
            print("\nNo active credentials found!")
        else:
            print(f"\nFound {len(active_accounts)} active credential(s):\n")
            for i, account in enumerate(active_accounts, 1):
                print(f"{i}. Login: {account['login']}")
                print(f"   Server: {account['server']}")
                print(f"   Key: {account['key']}")
                if account.get('assignedTo'):
                    print(f"   Assigned to: {account['assignedTo']}")
                if account.get('assignedOrderId'):
                    print(f"   Order ID: {account['assignedOrderId']}")
                print()
        
        mongo_db.close()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--active-only":
        view_active_only()
    else:
        view_all_credentials()
        print("\nTip: Run with --active-only flag to see only active credentials")

