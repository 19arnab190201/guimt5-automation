import os
import time
import json
from automation import automate_mt5_report
from parse import parse_mt5_report
from mongo_db import MT5MongoDB
import config

# Import configuration from config.py
MONGODB_URI = config.MONGODB_URI
MONGODB_DATABASE = config.MONGODB_DATABASE
SAVE_JSON_FILES = config.SAVE_JSON_FILES
INTER_ACCOUNT_DELAY = config.INTER_ACCOUNT_DELAY
SERVER = config.SERVER


def process_single_account(account, mongo_db=None):
    """
    Process a single trading account: automate, parse, and save to MongoDB
    
    Args:
        account: Dictionary with login, password, server
        mongo_db: MT5MongoDB instance (optional)
        
    Returns:
        True if successful, False otherwise
    """
    login = account['login']
    password = account['password']
    server = account['server']
    
    print("\n" + "=" * 80)
    print(f"Processing Account: {login}")
    print("=" * 80)
    
    # Step 1: Run automation for this account
    report_path = automate_mt5_report(login, password, server)
    
    if not report_path or not os.path.exists(report_path):
        print(f"Error: Report file not found for account {login}. Automation may have failed.")
        print(f"Report path: {report_path}")
        return False
    
    print(f"\nReport successfully saved at: {report_path}")
    
    # Step 2: Wait for file stability
    print("Waiting a few seconds for file write completion...")
    time.sleep(3)
    
    # Step 3: Parse the saved HTML report
    try:
        parsed_data = parse_mt5_report(report_path)
        print(f"\nReport parsing complete for account {login}.")
    except Exception as e:
        print(f"Error: Parsing failed for account {login}: {e}")
        return False
    
    # Step 4: Save to MongoDB
    if mongo_db:
        try:
            mongo_db.insert_or_update_account(parsed_data)
            print(f"Data saved to MongoDB for account {login}")
            
            # Update credential status after successful processing
            credential_key = account.get('key')
            mongo_db.update_credential_status(login, key=credential_key)
            
        except Exception as e:
            print(f"Error: MongoDB save failed for account {login}: {e}")
            # Continue even if MongoDB fails
    
    # Step 5: (Optional) Export structured JSON locally
    if SAVE_JSON_FILES:
        output_json = report_path.replace(".html", ".json")
        try:
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            print(f"JSON data saved to: {output_json}")
        except Exception as e:
            print(f"Warning: Failed to save JSON file: {e}")
    
    print(f"Account {login} processed successfully!")
    return True


def main():
    """Main function to process all accounts"""
    print("=" * 80)
    print("MT5 Multi-Account Automation + MongoDB Pipeline")
    print("=" * 80)
    
    # Initialize MongoDB connection
    mongo_db = None
    try:
        mongo_db = MT5MongoDB(connection_string=MONGODB_URI, database_name=MONGODB_DATABASE)
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
        print("Warning: Cannot continue without MongoDB connection (credentials are stored there)")
        return
    
    # Fetch active credentials from MongoDB
    print("\nFetching active credentials from MongoDB...")
    ACCOUNTS = mongo_db.get_active_credentials(server_name=SERVER)
    
    if not ACCOUNTS:
        print("Error: No active credentials found in MongoDB!")
        print("Please ensure credentials are added to the 'test/credentialkeys' collection")
        if mongo_db:
            mongo_db.close()
        return
    
    print(f"\nTotal active accounts to process: {len(ACCOUNTS)}")
    
    # Process each account
    results = {
        'success': [],
        'failed': []
    }
    
    for i, account in enumerate(ACCOUNTS, 1):
        print(f"\n\n{'='*80}")
        print(f"Processing account {i}/{len(ACCOUNTS)}")
        print(f"Key: {account.get('key', 'N/A')} | Login: {account['login']}")
        if account.get('assignedTo'):
            print(f"Assigned to: {account['assignedTo']}")
        print(f"{'='*80}")
        
        success = process_single_account(account, mongo_db)
        
        if success:
            results['success'].append(account['login'])
        else:
            results['failed'].append(account['login'])
        
        # Wait between accounts to avoid issues
        if i < len(ACCOUNTS):
            print(f"\nWaiting {INTER_ACCOUNT_DELAY} seconds before processing next account...")
            time.sleep(INTER_ACCOUNT_DELAY)
    
    # Close MongoDB connection
    if mongo_db:
        mongo_db.close()
    
    # Print summary
    print("\n" + "=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Successfully processed: {len(results['success'])} accounts")
    if results['success']:
        print(f"   Accounts: {', '.join(map(str, results['success']))}")
    
    print(f"\nFailed to process: {len(results['failed'])} accounts")
    if results['failed']:
        print(f"   Accounts: {', '.join(map(str, results['failed']))}")
    
    print("\n" + "=" * 80)
    print("Pipeline finished!")
    print("=" * 80)


if __name__ == "__main__":
    main()
