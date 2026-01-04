import os
import time
import json
from datetime import datetime
from automation import automate_mt5_report
from parse import parse_mt5_report
from mongo_db import MT5MongoDB
import config
from logger import setup_logger

# Import configuration from config.py
MONGODB_URI = config.MONGODB_URI
MONGODB_DATABASE = config.MONGODB_DATABASE
SAVE_JSON_FILES = config.SAVE_JSON_FILES
INTER_ACCOUNT_DELAY = config.INTER_ACCOUNT_DELAY
SERVER = config.SERVER

# Global logger instance (will be initialized in main())
logger = None


def process_single_account(account, mongo_db=None):
    """
    Process a single trading account: automate, parse, and save to MongoDB
    
    Args:
        account: Dictionary with login, password, server
        mongo_db: MT5MongoDB instance (optional)
        
    Returns:
        True if successful, False otherwise
    """
    global logger
    login = account['login']
    password = account['password']
    server = account['server']
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"Processing Account: {login}")
    logger.info("=" * 80)
    
    # Step 1: Run automation for this account
    logger.info(f"Starting automation for account {login}...")
    report_path = automate_mt5_report(login, password, server)
    
    if not report_path or not os.path.exists(report_path):
        logger.error(f"ERROR: Report file not found for account {login}. Automation may have failed.")
        logger.error(f"Report path: {report_path}")
        logger.info(f"STATUS: Account {login} - FAILED (Report file not found)")
        return False
    
    logger.info(f"Report successfully saved at: {report_path}")
    
    # Step 2: Wait for file stability
    logger.info("Waiting a few seconds for file write completion...")
    time.sleep(3)
    
    # Step 3: Parse the saved HTML report
    try:
        parsed_data = parse_mt5_report(report_path)
        logger.info(f"Report parsing complete for account {login}.")
    except Exception as e:
        logger.error(f"ERROR: Parsing failed for account {login}: {e}")
        logger.info(f"STATUS: Account {login} - FAILED (Parsing error)")
        return False
    
    # Step 4: Save to MongoDB
    if mongo_db:
        try:
            mongo_db.insert_or_update_account(parsed_data)
            logger.info(f"Data saved to MongoDB for account {login}")
            
            # Update credential status after successful processing
            credential_key = account.get('key')
            mongo_db.update_credential_status(login, key=credential_key)
            
        except Exception as e:
            logger.error(f"ERROR: MongoDB save failed for account {login}: {e}")
            # Continue even if MongoDB fails
    
    # Step 5: (Optional) Export structured JSON locally
    if SAVE_JSON_FILES:
        output_json = report_path.replace(".html", ".json")
        try:
            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=4)
            logger.info(f"JSON data saved to: {output_json}")
        except Exception as e:
            logger.warning(f"WARNING: Failed to save JSON file: {e}")
    
    logger.info(f"STATUS: Account {login} - SUCCESS")
    return True


def main():
    """Main function to process all accounts"""
    global logger
    
    # Initialize logger
    logger_instance, log_file_path = setup_logger()
    logger = logger_instance
    
    # Log STARTING TIME
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info("=" * 80)
    logger.info("MT5 Multi-Account Automation + MongoDB Pipeline")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"STARTING TIME: {start_time}")
    logger.info("")
    logger.info(f"Log file: {log_file_path}")
    logger.info("")
    
    # Initialize MongoDB connection
    mongo_db = None
    try:
        logger.info("Connecting to MongoDB...")
        mongo_db = MT5MongoDB(connection_string=MONGODB_URI, database_name=MONGODB_DATABASE)
        logger.info("MongoDB connection established.")
    except Exception as e:
        logger.error(f"ERROR: MongoDB connection failed: {e}")
        logger.error("ERROR: Cannot continue without MongoDB connection (credentials are stored there)")
        return
    
    # Fetch active credentials from MongoDB
    logger.info("Fetching active credentials from MongoDB...")
    ACCOUNTS = mongo_db.get_active_credentials(server_name=SERVER)
    
    if not ACCOUNTS:
        logger.error("ERROR: No active credentials found in MongoDB!")
        logger.error("Please ensure credentials are added to the 'test/credentialkeys' collection")
        if mongo_db:
            mongo_db.close()
        return
    
    logger.info(f"Total active accounts to process: {len(ACCOUNTS)}")
    logger.info("")
    
    # Process each account
    results = {
        'success': [],
        'failed': []
    }
    
    for i, account in enumerate(ACCOUNTS, 1):
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"Processing account {i}/{len(ACCOUNTS)}")
        logger.info(f"Key: {account.get('key', 'N/A')} | Login: {account['login']}")
        if account.get('assignedTo'):
            logger.info(f"Assigned to: {account['assignedTo']}")
        logger.info("=" * 80)
        
        success = process_single_account(account, mongo_db)
        
        if success:
            results['success'].append(account['login'])
        else:
            results['failed'].append(account['login'])
        
        # Add spacing between accounts
        logger.info("")
        logger.info("-" * 80)
        
        # Wait between accounts to avoid issues
        if i < len(ACCOUNTS):
            logger.info(f"Waiting {INTER_ACCOUNT_DELAY} seconds before processing next account...")
            time.sleep(INTER_ACCOUNT_DELAY)
            logger.info("")
    
    # Close MongoDB connection
    if mongo_db:
        mongo_db.close()
        logger.info("MongoDB connection closed.")
    
    # Log FINAL SUMMARY
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Start Time: {start_time}")
    logger.info(f"End Time: {end_time}")
    logger.info("")
    logger.info(f"Successfully processed: {len(results['success'])} accounts")
    if results['success']:
        logger.info(f"   Accounts: {', '.join(map(str, results['success']))}")
    
    logger.info(f"")
    logger.info(f"Failed to process: {len(results['failed'])} accounts")
    if results['failed']:
        logger.info(f"   Accounts: {', '.join(map(str, results['failed']))}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Pipeline finished!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
