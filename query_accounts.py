"""
Utility script to query and display trading accounts from MongoDB
"""
from mongo_db import MT5MongoDB
import config
from datetime import datetime
import json


def display_account_summary(account):
    """Display a summary of a trading account"""
    acc_info = account.get('account', {})
    summary = account.get('summary', {})
    balance = account.get('balance', {})
    
    print("\n" + "=" * 70)
    print(f"Account: {acc_info.get('account')} - {acc_info.get('name')}")
    print("=" * 70)
    print(f"Broker:          {acc_info.get('broker')}")
    print(f"Type:            {acc_info.get('type')}")
    print(f"Currency:        {acc_info.get('currency')}")
    print(f"Balance:         {balance.get('balance', 0):.2f}")
    print(f"Equity:          {balance.get('equity', 0):.2f}")
    print(f"Gain:            {summary.get('gain', 0):.2f}%")
    print(f"Deposits:        {summary.get('deposit', [0, 0])[0]:.2f}")
    print(f"Withdrawals:     {summary.get('withdrawal', [0, 0])[0]:.2f}")
    
    # Long/Short stats
    long_short_total = account.get('longShortTotal', {})
    long_trades = long_short_total.get('long', 0)
    short_trades = long_short_total.get('short', 0)
    total_trades = long_trades + short_trades
    
    print(f"\nTotal Trades:    {total_trades}")
    print(f"Long Trades:     {long_trades} ({long_trades/total_trades*100:.1f}%)" if total_trades else "Long Trades:     0")
    print(f"Short Trades:    {short_trades} ({short_trades/total_trades*100:.1f}%)" if total_trades else "Short Trades:    0")
    
    # Timestamps
    if 'updatedAt' in account:
        print(f"\nLast Updated:    {account['updatedAt']}")


def list_all_accounts():
    """List all trading accounts in MongoDB"""
    print("\n" + "=" * 70)
    print("ALL TRADING ACCOUNTS IN DATABASE")
    print("=" * 70)
    
    db = MT5MongoDB(connection_string=config.MONGODB_URI, database_name=config.MONGODB_DATABASE)
    
    accounts = db.get_all_accounts()
    
    if not accounts:
        print("\n❌ No accounts found in database")
        db.close()
        return
    
    print(f"\nFound {len(accounts)} account(s)\n")
    
    for i, account in enumerate(accounts, 1):
        acc_info = account.get('account', {})
        balance = account.get('balance', {})
        summary = account.get('summary', {})
        
        print(f"{i}. Account {acc_info.get('account')} - {acc_info.get('name')}")
        print(f"   Balance: {balance.get('balance', 0):.2f} {acc_info.get('currency', 'USD')}")
        print(f"   Gain: {summary.get('gain', 0):.2f}%")
        print(f"   Broker: {acc_info.get('broker')}")
        print()
    
    db.close()


def get_account_details(account_number):
    """Get detailed information for a specific account"""
    db = MT5MongoDB(connection_string=config.MONGODB_URI, database_name=config.MONGODB_DATABASE)
    
    account = db.get_account_by_number(account_number)
    
    if not account:
        print(f"\n❌ Account {account_number} not found in database")
        db.close()
        return
    
    display_account_summary(account)
    
    # Option to export full data
    print("\n" + "-" * 70)
    export = input("\nExport full account data to JSON? (y/n): ").lower().strip()
    
    if export == 'y':
        filename = f"account_{account_number}_export.json"
        # Remove MongoDB's _id field for cleaner JSON
        if '_id' in account:
            del account['_id']
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(account, f, indent=2, default=str)
        
        print(f"✅ Exported to {filename}")
    
    db.close()


def get_top_performers(limit=5):
    """Get top performing accounts by gain"""
    print("\n" + "=" * 70)
    print(f"TOP {limit} PERFORMING ACCOUNTS")
    print("=" * 70)
    
    db = MT5MongoDB(connection_string=config.MONGODB_URI, database_name=config.MONGODB_DATABASE)
    
    # Get all accounts and sort by gain
    accounts = db.get_all_accounts()
    
    if not accounts:
        print("\n❌ No accounts found in database")
        db.close()
        return
    
    # Sort by gain
    sorted_accounts = sorted(accounts, key=lambda x: x.get('summary', {}).get('gain', 0), reverse=True)
    
    for i, account in enumerate(sorted_accounts[:limit], 1):
        acc_info = account.get('account', {})
        summary = account.get('summary', {})
        balance = account.get('balance', {})
        
        print(f"\n{i}. Account {acc_info.get('account')} - {acc_info.get('name')}")
        print(f"   Gain:     {summary.get('gain', 0):.2f}%")
        print(f"   Balance:  {balance.get('balance', 0):.2f} {acc_info.get('currency', 'USD')}")
        print(f"   Broker:   {acc_info.get('broker')}")
    
    db.close()


def main():
    """Main menu for querying accounts"""
    while True:
        print("\n" + "=" * 70)
        print("MT5 TRADING ACCOUNTS - QUERY TOOL")
        print("=" * 70)
        print("\n1. List all accounts")
        print("2. Get account details")
        print("3. Top performing accounts")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            list_all_accounts()
        
        elif choice == '2':
            try:
                account_num = int(input("\nEnter account number: ").strip())
                get_account_details(account_num)
            except ValueError:
                print("❌ Invalid account number")
        
        elif choice == '3':
            try:
                limit = input("\nHow many top accounts to show? (default 5): ").strip()
                limit = int(limit) if limit else 5
                get_top_performers(limit)
            except ValueError:
                print("❌ Invalid number")
        
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

