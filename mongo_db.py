"""
MongoDB integration module for MT5 trading account data
"""
import os
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime


class MT5MongoDB:
    """Handler for MongoDB operations related to MT5 trading accounts"""
    
    def __init__(self, connection_string=None, database_name="test"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection URI (defaults to env variable MONGODB_URI)
            database_name: Name of the database to use
        """
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db['credentials_reports']
        self.credentials_collection = self.db['credentialkeys']
        
        # Test connection
        try:
            self.client.admin.command('ping')
            print(f"Connected to MongoDB: {database_name}")
        except ConnectionFailure:
            print("MongoDB connection failed!")
            raise
    
    def transform_mt5_data(self, parsed_data):
        """
        Transform parsed MT5 report data to match MongoDB schema
        
        Args:
            parsed_data: Dictionary from parse_mt5_report function
            
        Returns:
            Dictionary matching TradingAccount schema
        """
        account_info = parsed_data.get('account', {})
        summary = parsed_data.get('summary', {})
        balance_data = parsed_data.get('balance', {})
        growth_data = parsed_data.get('growth', {})
        dividend_data = parsed_data.get('dividend', {})
        profit_total = parsed_data.get('profitTotal', {})
        profit_money = parsed_data.get('profitMoney', {})
        profit_deals = parsed_data.get('profitDeals', {})
        profit_daily = parsed_data.get('profitDaily', {})
        profit_type = parsed_data.get('profitType', {})
        long_short_total = parsed_data.get('longShortTotal', {})
        long_short = parsed_data.get('longShort', {})
        long_short_daily = parsed_data.get('longShortDaily', {})
        long_short_indicators = parsed_data.get('longShortIndicators', {})
        trade_type_total = parsed_data.get('tradeTypeTotal', {})
        symbol_money = parsed_data.get('symbolMoney', {})
        symbol_deals = parsed_data.get('symbolDeals', {})
        symbol_indicators = parsed_data.get('symbolIndicators', {})
        symbols_total = parsed_data.get('symbolsTotal', {})
        symbol_types = parsed_data.get('symbolTypes', {})
        drawdown = parsed_data.get('drawdown', {})
        risks_indicators = parsed_data.get('risksIndicators', {})
        risks_mfe_mae_percent = parsed_data.get('risksMfeMaePercent', {})
        risks_mfe_mae_money = parsed_data.get('risksMfeMaeMoney', {})
        summary_indicators = parsed_data.get('summaryIndicators', {})
        
        # Build the document according to schema
        document = {
            'name': account_info.get('name', ''),
            'currency': account_info.get('currency', 'USD'),
            'type': account_info.get('type', 'demo'),
            'broker': account_info.get('broker', ''),
            'account': account_info.get('account', 0),
            'digits': account_info.get('digits', 2),
            'summary': {
                'gain': summary.get('gain', 0),
                'activity': summary.get('activity', 0),
                'deposit': summary.get('deposit', [0, 0]),
                'withdrawal': summary.get('withdrawal', [0, 0]),
                'dividend': summary.get('dividend', 0),
                'correction': summary.get('correction', 0),
                'credit': summary.get('credit', 0)
            },
            'summaryIndicators': {
                'sharp_ratio': summary_indicators.get('sharp_ratio'),
                'profit_factor': summary_indicators.get('profit_factor'),
                'recovery_factor': summary_indicators.get('recovery_factor'),
                'drawdown': summary_indicators.get('drawdown'),
                'deposit_load': summary_indicators.get('deposit_load'),
                'trades_per_week': summary_indicators.get('trades_per_week'),
                'hold_time': summary_indicators.get('hold_time')
            },
            'balance': {
                'balance': balance_data.get('balance', 0),
                'equity': balance_data.get('equity', 0),
                'period': balance_data.get('period', 0),
                'chart': balance_data.get('chart', []),
                'table': balance_data.get('table', {'years': [], 'total': 0})
            },
            'growth': {
                'growth': growth_data.get('growth', 0),
                'drawdown': growth_data.get('drawdown', 0),
                'period': growth_data.get('period', 0),
                'chart': growth_data.get('chart', []),
                'table': growth_data.get('table', {'years': [], 'total': 0})
            },
            'dividend': {
                'dividend': dividend_data.get('dividend', 0),
                'correction': dividend_data.get('correction', 0),
                'credit': dividend_data.get('credit', 0),
                'period': dividend_data.get('period', 0),
                'chart': dividend_data.get('chart', []),
                'table': dividend_data.get('table', {'years': [], 'total': 0})
            },
            'profitTotal': {
                'profit': profit_total.get('profit', 0),
                'profit_gross': profit_total.get('profit_gross', 0),
                'profit_dividend': profit_total.get('profit_dividend', 0),
                'profit_swap': profit_total.get('profit_swap', 0),
                'loss': profit_total.get('loss', 0),
                'loss_gross': profit_total.get('loss_gross', 0),
                'loss_commission': profit_total.get('loss_commission', 0)
            },
            'profitMoney': {
                'period': profit_money.get('period', 0),
                'profit': profit_money.get('profit', []),
                'loss': profit_money.get('loss', []),
                'table': profit_money.get('table', {'years': [], 'total': 0})
            },
            'profitDeals': {
                'period': profit_deals.get('period', 0),
                'profit': profit_deals.get('profit', []),
                'loss': profit_deals.get('loss', []),
                'table': profit_deals.get('table', {'years': [], 'total': 0})
            },
            'profitDaily': {
                'chart': profit_daily.get('chart', [])
            },
            'profitType': {
                'robot': profit_type.get('robot', {'x': 0, 'y': [0, 0]}),
                'manual': profit_type.get('manual', {'x': 0, 'y': [0, 0]}),
                'signals': profit_type.get('signals', {'x': 0, 'y': [0, 0]})
            },
            'longShortTotal': {
                'long': long_short_total.get('long', 0),
                'short': long_short_total.get('short', 0)
            },
            'longShort': {
                'period': long_short.get('period', 0),
                'long': long_short.get('long', []),
                'short': long_short.get('short', []),
                'all': long_short.get('all', [])
            },
            'longShortDaily': {
                'chart': long_short_daily.get('chart', [])
            },
            'longShortIndicators': {
                'netto_pl': long_short_indicators.get('netto_pl', [0, 0]),
                'average_pl': long_short_indicators.get('average_pl', [0, 0]),
                'average_pl_percent': long_short_indicators.get('average_pl_percent', [0, 0]),
                'commissions': long_short_indicators.get('commissions', [0, 0]),
                'average_profit': long_short_indicators.get('average_profit', [0, 0]),
                'average_profit_percent': long_short_indicators.get('average_profit_percent', [0, 0]),
                'trades': long_short_indicators.get('trades', [0, 0]),
                'win_trades': long_short_indicators.get('win_trades', [0, 0])
            },
            'tradeTypeTotal': {
                'robots': trade_type_total.get('robots', 0),
                'manual': trade_type_total.get('manual', 0),
                'signals': trade_type_total.get('signals', 0)
            },
            'symbolMoney': {
                'period': symbol_money.get('period', 0),
                'chart': symbol_money.get('chart', [])
            },
            'symbolDeals': {
                'period': symbol_deals.get('period', 0),
                'chart': symbol_deals.get('chart', [])
            },
            'symbolIndicators': {
                'profit_factor': symbol_indicators.get('profit_factor', []),
                'netto_profit': symbol_indicators.get('netto_profit', []),
                'fees': symbol_indicators.get('fees', [])
            },
            'symbolsTotal': {
                'total': symbols_total.get('total', [])
            },
            'symbolTypes': {
                'type': symbol_types.get('type', [])
            },
            'drawdown': {
                'drawdown': drawdown.get('drawdown', 0),
                'deposit_load': drawdown.get('deposit_load', 0),
                'period': drawdown.get('period', 0),
                'chart': drawdown.get('chart', [])
            },
            'risksIndicators': {
                'profit': risks_indicators.get('profit', [0, 0]),
                'max_consecutive_trades': risks_indicators.get('max_consecutive_trades', [0, 0]),
                'max_consecutive_profit': risks_indicators.get('max_consecutive_profit', [0, 0])
            },
            'risksMfeMaePercent': {
                'max_avg_profit_ratio': risks_mfe_mae_percent.get('max_avg_profit_ratio', 0),
                'max_avg_mfe_ratio': risks_mfe_mae_percent.get('max_avg_mfe_ratio', 0),
                'min_avg_loss_ratio': risks_mfe_mae_percent.get('min_avg_loss_ratio', 0),
                'min_avg_mae_ratio': risks_mfe_mae_percent.get('min_avg_mae_ratio', 0),
                'period': risks_mfe_mae_percent.get('period', 0),
                'chart': risks_mfe_mae_percent.get('chart', [])
            },
            'risksMfeMaeMoney': {
                'max_avg_profit': risks_mfe_mae_money.get('max_avg_profit', 0),
                'max_avg_mfe': risks_mfe_mae_money.get('max_avg_mfe', 0),
                'min_avg_loss': risks_mfe_mae_money.get('min_avg_loss', 0),
                'min_avg_mae': risks_mfe_mae_money.get('min_avg_mae', 0),
                'period': risks_mfe_mae_money.get('period', 0),
                'chart': risks_mfe_mae_money.get('chart', [])
            }
        }
        
        return document
    
    def insert_or_update_account(self, parsed_data):
        """
        Insert or update a trading account in MongoDB
        
        Args:
            parsed_data: Dictionary from parse_mt5_report function
            
        Returns:
            The inserted/updated document ID
        """
        document = self.transform_mt5_data(parsed_data)
        account_number = document['account']
        
        try:
            # Use upsert to insert or update based on account number
            result = self.collection.update_one(
                {'account': account_number},
                {
                    '$set': document,
                    '$currentDate': {'updatedAt': True}
                },
                upsert=True
            )
            
            if result.upserted_id:
                print(f"Inserted new account {account_number} into MongoDB")
                return result.upserted_id
            else:
                print(f"Updated existing account {account_number} in MongoDB")
                return account_number
                
        except DuplicateKeyError:
            print(f"Warning: Account {account_number} already exists, updating...")
            result = self.collection.replace_one(
                {'account': account_number},
                document
            )
            return account_number
        except Exception as e:
            print(f"Error: MongoDB operation failed: {e}")
            raise
    
    def get_account_by_number(self, account_number):
        """Retrieve an account by account number"""
        return self.collection.find_one({'account': account_number})
    
    def get_all_accounts(self):
        """Retrieve all trading accounts"""
        return list(self.collection.find())
    
    def delete_account(self, account_number):
        """Delete an account by account number"""
        result = self.collection.delete_one({'account': account_number})
        return result.deleted_count > 0
    
    def get_active_credentials(self, server_name="Exness-MT5Trial8"):
        """
        Fetch all active credentials from the credentials collection
        
        Args:
            server_name: MT5 server name to use for all accounts
            
        Returns:
            List of account dictionaries with login, password, and server
        """
        try:
            # Find all documents in the credentials collection
            credential_docs = list(self.credentials_collection.find())
            
            active_accounts = []
            
            for doc in credential_docs:
                key = doc.get('key', 'Unknown')
                credentials = doc.get('credentials', [])
                
                # Filter for active and non-breached credentials only
                for cred in credentials:
                    is_active = cred.get('isActive', False)
                    # Default to False if isBreached field doesn't exist
                    # Only considered breached if explicitly set to True
                    is_breached = cred.get('isBreached', False)
                    
                    # Only process if active AND not breached
                    if is_active and not is_breached:
                        account = {
                            'login': int(cred['loginId']),
                            'password': cred['password'],
                            'server': server_name,
                            'key': key,  # Store the key for reference
                            'assignedTo': cred.get('assignedTo'),
                            'assignedOrderId': cred.get('assignedOrderId')
                        }
                        active_accounts.append(account)
            
            print(f"Found {len(active_accounts)} active credentials in MongoDB")
            return active_accounts
            
        except Exception as e:
            print(f"Error: Failed to fetch credentials from MongoDB: {e}")
            return []
    
    def update_credential_status(self, login_id, key=None):
        """
        Update credential status after processing
        
        Args:
            login_id: The MT5 login ID (account number)
            key: The credential key/group (optional, for faster lookup)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from datetime import datetime
            
            # Build the query
            query = {"credentials.loginId": str(login_id)}
            if key:
                query["key"] = key
            
            # Update the credential
            update_result = self.credentials_collection.update_one(
                query,
                {
                    "$set": {
                        "credentials.$.lastChecked": datetime.utcnow(),
                        "credentials.$.isBreached": False,
                        "credentials.$.breachedMetadata": "will be known soon",
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            if update_result.modified_count > 0:
                print(f"Updated credential status for login {login_id}")
                return True
            else:
                print(f"Warning: No credential found to update for login {login_id}")
                return False
                
        except Exception as e:
            print(f"Error: Failed to update credential status for login {login_id}: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection"""
        self.client.close()
        print("MongoDB connection closed")


if __name__ == "__main__":
    # Test the MongoDB connection
    try:
        db = MT5MongoDB()
        print("MongoDB connection test successful!")
        db.close()
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")

