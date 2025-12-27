"""
MongoDB integration module for MT5 trading account data
"""
import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure, DuplicateKeyError


class MT5MongoDB:
    """Handler for MongoDB operations related to MT5 trading accounts"""

    STATUS_ACTIVE = "ACTIVE"
    STATUS_BREACHED = "BREACHED"
    STATUS_UNDER_REVIEW = "UNDER REVIEW"

    RULES = {
        "2_STEP_PHASE_1": {
            "profit_target": 0.08,
            "max_loss_limit": 0.08,
            "daily_loss_limit": 0.04,
            "leverage": "1:100",
            "min_profitable_days": 3,
            "max_inactivity_days": 14,
        },
        "2_STEP_PHASE_2": {
            "profit_target": 0.05,
            "max_loss_limit": 0.08,
            "daily_loss_limit": 0.04,
            "leverage": "1:100",
            "min_profitable_days": 3,
            "max_inactivity_days": 14,
        },
        "1_STEP": {
            "profit_target": 0.10,
            "max_loss_limit": 0.06,
            "daily_loss_limit": 0.03,
            "leverage": "1:50",
            "min_profitable_days": 3,
            "max_inactivity_days": 14,
        },
    }
    
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
    
    def _parse_iso_date(self, value):
        """Parse various date formats found in Mongo/MT5 payloads."""
        try:
            if isinstance(value, datetime):
                return value
            if isinstance(value, dict) and "$date" in value:
                return datetime.fromisoformat(value["$date"].replace("Z", "+00:00")).astimezone(timezone.utc)
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            return None
        return None

    def _find_credential_key(self, account_number):
        """Lookup credential key from credentialkeys collection for a login (match string or number)."""
        if account_number is None:
            return None
        try:
            variants = [str(account_number)]
            try:
                variants.append(int(account_number))
            except Exception:
                pass

            doc = self.credentials_collection.find_one(
                {"credentials": {"$elemMatch": {"loginId": {"$in": variants}}}},
                {"key": 1}
            )
            if doc and doc.get("key"):
                return doc["key"]
        except Exception:
            pass
        return None

    def _infer_program(self, account_name: str, credential_key: str = None):
        """
        Infer challenge program from account name.
        Fallback priority:
        1) credential key suffix (e.g., 1STEP/2STEP)
        2) name keywords
        3) default to 2_STEP_PHASE_1
        """
        if credential_key:
            key_upper = credential_key.upper()
            if "1STEP" in key_upper:
                return "1_STEP"
            if "2STEP" in key_upper:
                return "2_STEP_PHASE_1"

        lowered = (account_name or "").lower()
        if "1 step" in lowered or "one step" in lowered:
            return "1_STEP"
        if "phase 2" in lowered or "step 2" in lowered or "phase two" in lowered:
            return "2_STEP_PHASE_2"
        return "2_STEP_PHASE_1"

    def _group_chart_by_day(self, balance_chart):
        """
        Group balance chart points by UTC date.
        Returns dict: {date: [list of points sorted by timestamp]}
        Each point has: {'timestamp': datetime, 'balance': float, 'equity': float}
        """
        daily_data = {}
        
        for point in balance_chart:
            ts = datetime.fromtimestamp(point.get("x", 0), tz=timezone.utc)
            y_vals = point.get("y", [0, 0])
            
            if not isinstance(y_vals, list) or len(y_vals) < 2:
                continue
                
            day_key = ts.date()
            if day_key not in daily_data:
                daily_data[day_key] = []
            
            daily_data[day_key].append({
                'timestamp': ts,
                'balance': float(y_vals[0] or 0),
                'equity': float(y_vals[1] or 0)
            })
        
        # Sort each day's points by timestamp
        for day_key in daily_data:
            daily_data[day_key].sort(key=lambda x: x['timestamp'])
        
        return daily_data

    def _get_midnight_utc_value(self, day_date, daily_data):
        """
        Returns max(balance, equity) at 00:00 UTC for the given day.
        Uses the latest data point AT OR BEFORE midnight.
        Never looks forward in time.
        
        Strategy:
        1. Search ALL points in daily_data to find the latest point <= midnight UTC
        2. This ensures we find the point even if it's in the current day's list
        """
        midnight_utc = datetime(
            day_date.year,
            day_date.month,
            day_date.day,
            tzinfo=timezone.utc
        )

        latest_point = None

        # Search through ALL days to find the latest point at or before midnight
        for date_key, points in daily_data.items():
            for p in points:
                # Only consider points at or before midnight UTC of target day
                if p["timestamp"] <= midnight_utc:
                    # Keep track of the latest point
                    if latest_point is None or p["timestamp"] > latest_point["timestamp"]:
                        latest_point = p

        if latest_point:
            return max(latest_point["balance"], latest_point["equity"])

        return None

    def _check_daily_drawdown(self, balance_chart, daily_loss_limit, initial_balance=None):
        """
        Checks Daily Drawdown across all UTC days.

        Rule:
        - Daily reference = max(balance, equity) at 00:00 UTC
        - Reference comes from latest value <= midnight
        - Rolling high-watermark equity during the day
        - Breach if equity drops more than daily_loss_limit from peak
        """
        if not balance_chart:
            return False, {}

        daily_data = self._group_chart_by_day(balance_chart)
        if not daily_data:
            return False, {}

        sorted_days = sorted(daily_data.keys())

        worst_breach_amount = None
        worst_breach_details = {}

        for i, day_date in enumerate(sorted_days):
            day_points = daily_data.get(day_date, [])
            if not day_points:
                continue

            # --- Midnight reference (critical) ---
            midnight_value = self._get_midnight_utc_value(day_date, daily_data)

            # First day fallback to initial_balance ONLY if truly needed
            if midnight_value is None:
                if i == 0 and initial_balance and initial_balance > 0:
                    midnight_reference = initial_balance
                else:
                    continue  # cannot evaluate this day safely
            else:
                midnight_reference = midnight_value

            if midnight_reference <= 0:
                continue

            # Threshold is ALWAYS based on midnight UTC value, not rolling peak
            threshold = midnight_reference * (1 - daily_loss_limit)
            
            # Track rolling high watermark for display/metrics
            peak_equity = midnight_reference
            day_breached = False
            breach_info = None
            max_dd_pct = 0.0

            for point in day_points:
                equity = point["equity"]

                # rolling high watermark (for tracking, but threshold stays based on midnight)
                if equity > peak_equity:
                    peak_equity = equity

                # Check breach against threshold based on midnight value

                if equity < threshold and not day_breached:
                    day_breached = True
                    breach_info = {
                        "breach_date": str(day_date),
                        "timestamp": point["timestamp"],
                        "peak_equity": peak_equity,  # Current peak (rolling high watermark)
                        "midnight_reference": midnight_reference,  # Base value at 00:00 UTC
                        "threshold": threshold,  # Based on midnight_reference, not peak
                        "equity_at_breach": equity,
                    }

                if peak_equity > 0:
                    dd_pct = (peak_equity - equity) / peak_equity
                    max_dd_pct = max(max_dd_pct, dd_pct)

            if day_breached and breach_info:
                breach_amount = breach_info["threshold"] - breach_info["equity_at_breach"]

                if worst_breach_amount is None or breach_amount > worst_breach_amount:
                    worst_breach_amount = breach_amount
                    worst_breach_details = {
                        **breach_info,
                        "breach_amount": breach_amount,
                        "max_drawdown_percent": max_dd_pct,
                    }

        # --- Current day metrics ---
        current_day = sorted_days[-1]
        current_points = daily_data.get(current_day, [])

        details = {
            "total_days_checked": len(sorted_days),
            "current_day": str(current_day),
            "allowed_drawdown_percent": daily_loss_limit,
        }

        if current_points:
            curr_midnight = self._get_midnight_utc_value(current_day, daily_data)

            if curr_midnight is None:
                curr_midnight_ref = initial_balance if initial_balance else 0
            else:
                curr_midnight_ref = curr_midnight

            # Threshold is based on midnight reference, not rolling peak
            curr_threshold = curr_midnight_ref * (1 - daily_loss_limit) if curr_midnight_ref > 0 else 0
            
            # Track rolling peak for display
            curr_peak = curr_midnight_ref
            for p in current_points:
                if p["equity"] > curr_peak:
                    curr_peak = p["equity"]
            curr_equity = current_points[-1]["equity"]
            curr_dd_pct = (
                (curr_peak - curr_equity) / curr_peak if curr_peak > 0 else 0
            )

            details.update({
                "current_peak_equity": curr_peak,
                "current_threshold": curr_threshold,
                "current_equity": curr_equity,
                "current_drawdown_percent": curr_dd_pct,
            })

        is_breached = worst_breach_amount is not None

        if is_breached:
            details.update(worst_breach_details)

        return is_breached, details

    def _count_profitable_days(self, profit_daily_chart, initial_balance):
        """
        Count days with at least 1.5% profit from profitDaily.chart.
        Each day must have net profit >= 1.5% of initial balance (gaps allowed, not consecutive required).
        """
        if not initial_balance or initial_balance <= 0:
            return 0
        
        min_profit_threshold = initial_balance * 0.015  # 1.5%
        profitable = 0
        
        for entry in profit_daily_chart or []:
            y_vals = entry.get("y", [])
            day_net = 0
            for val in y_vals:
                if isinstance(val, (int, float)):
                    day_net += val
            
            # Day is profitable if net profit >= 1.5% of initial balance
            if day_net >= min_profit_threshold:
                profitable += 1
        
        return profitable
    
    def _check_inactivity_breach(self, balance_chart, max_inactivity_days):
        """
        Check for consecutive days with no equity change.
        Returns (is_breached, consecutive_days_without_change)
        """
        if not balance_chart or len(balance_chart) < 2:
            return False, 0
        
        # Group points by UTC day
        daily_equity = {}  # date -> equity value
        for point in balance_chart:
            ts = datetime.fromtimestamp(point.get("x", 0), tz=timezone.utc)
            day_key = ts.date()
            equity = point.get("y", [0, 0])[1] if isinstance(point.get("y"), list) else point.get("y", 0)
            # Store the last equity value for each day
            if day_key not in daily_equity:
                daily_equity[day_key] = equity
        
        # Sort by date
        sorted_dates = sorted(daily_equity.keys())
        if len(sorted_dates) < 2:
            return False, 0
        
        # Check for consecutive days with same equity
        max_consecutive = 0
        current_consecutive = 1
        
        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i - 1]
            curr_date = sorted_dates[i]
            prev_equity = daily_equity[prev_date]
            curr_equity = daily_equity[curr_date]
            
            # Check if equity is unchanged (within small tolerance for floating point)
            if abs(curr_equity - prev_equity) < 0.01:
                current_consecutive += 1
            else:
                max_consecutive = max(max_consecutive, current_consecutive)
                current_consecutive = 1
        
        max_consecutive = max(max_consecutive, current_consecutive)
        
        is_breached = max_consecutive > max_inactivity_days
        return is_breached, max_consecutive

    def _evaluate_account(self, parsed_data, credential_key=None):
        """Apply breach rules and return evaluation metadata."""
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        account_info = parsed_data.get("account", {})
        summary = parsed_data.get("summary", {})
        balance_block = parsed_data.get("balance", {})
        summary_indicators = parsed_data.get("summaryIndicators", {})

        account_name = account_info.get("name", "") or ""
        program = self._infer_program(account_name, credential_key)
        rules = self.RULES[program]

        initial_balance = float(summary.get("deposit", [0, 0])[0] or 0)
        current_balance = float(balance_block.get("balance", 0) or 0)
        current_equity = float(balance_block.get("equity", 0) or 0)
        balance_chart = balance_block.get("chart", []) or []

        breaches = []
        consecutive_inactive_days = 0  # Initialize for metrics

        # Maximum loss limit check (critical)
        if initial_balance > 0:
            min_balance = min((pt.get("y", [0, 0])[0] for pt in balance_chart), default=current_balance)
            min_equity = min((pt.get("y", [0, 0])[1] for pt in balance_chart), default=current_equity)
            worst_value = min(min_balance, min_equity)
            threshold = initial_balance * (1 - rules["max_loss_limit"])
            if worst_value < threshold:
                breaches.append(
                    {
                        "rule": "MAX_LOSS_LIMIT",
                        "severity": "critical",
                        "observed": worst_value,
                        "threshold": threshold,
                        "message": "Minimum balance/equity fell below maximum loss limit.",
                    }
                )

        # Daily Drawdown check (critical)
        # Checks ALL days: if equity dropped more than allowed % from the PEAK equity reached during each day
        daily_dd_breached, daily_dd_details = self._check_daily_drawdown(
            balance_chart, rules["daily_loss_limit"], initial_balance
        )
        if daily_dd_breached:
            breach_date = daily_dd_details.get("breach_date", "unknown")
            peak = daily_dd_details.get("peak_equity", 0)
            thresh = daily_dd_details.get("threshold", 0)
            breach_eq = daily_dd_details.get("equity_at_breach", 0)
            breaches.append(
                {
                    "rule": "DAILY_DRAWDOWN",
                    "severity": "critical",
                    "breach_date": breach_date,
                    "observed": breach_eq,
                    "threshold": thresh,
                    "peak_equity": peak,
                    "message": f"Daily drawdown breached on {breach_date}. Peak: ${peak:,.2f}, Threshold: ${thresh:,.2f}, Dropped to: ${breach_eq:,.2f}",
                }
            )

        # Inactivity breach check (critical) - consecutive days with no equity change
        inactivity_breached, consecutive_inactive_days = self._check_inactivity_breach(
            balance_chart, rules["max_inactivity_days"]
        )
        # consecutive_inactive_days is now set for metrics
        if inactivity_breached:
            breaches.append(
                {
                    "rule": "INACTIVITY",
                    "severity": "critical",
                    "observed": consecutive_inactive_days,
                    "threshold": rules["max_inactivity_days"],
                    "message": f"Equity unchanged for {consecutive_inactive_days} consecutive days (exceeds {rules['max_inactivity_days']} day limit).",
                }
            )

        # Minimum profitable days check (NOT a breach, only for UNDER REVIEW status)
        # Each day must have >= 1.5% profit (gaps allowed, not consecutive required)
        profit_daily_chart = parsed_data.get("profitDaily", {}).get("chart", [])
        profitable_days = self._count_profitable_days(profit_daily_chart, initial_balance)

        # Profit target
        profit_target_hit = False
        profit_percent = None
        if initial_balance > 0:
            profit_percent = (current_equity - initial_balance) / initial_balance
            profit_target_hit = profit_percent >= rules["profit_target"]

        # Status derivation
        status = self.STATUS_ACTIVE
        is_breached = False
        if breaches:
            status = self.STATUS_BREACHED
            is_breached = True
        elif profit_target_hit and profitable_days >= rules["min_profitable_days"]:
            status = self.STATUS_UNDER_REVIEW

        evaluation = {
            "program": program,
            "rulesApplied": rules,
            "evaluatedAt": now,
            "status": status,
            "isBreached": is_breached,
            "breaches": breaches,
            "breachReasons": [b["rule"] for b in breaches],
            "credentialKey": credential_key,
            "metrics": {
                "initial_balance": initial_balance,
                "current_balance": current_balance,
                "current_equity": current_equity,
                "worst_balance_or_equity": min_balance if initial_balance > 0 else None,
                "profit_percent": profit_percent,
                "profit_target_hit": profit_target_hit,
                "profitable_days": profitable_days,
                "consecutive_inactive_days": consecutive_inactive_days,
                # Daily Drawdown metrics (current day)
                "daily_dd_total_days_checked": daily_dd_details.get("total_days_checked"),
                "daily_dd_peak_equity": daily_dd_details.get("current_peak_equity"),
                "daily_dd_threshold": daily_dd_details.get("current_threshold"),
                "daily_dd_current_drawdown_pct": daily_dd_details.get("current_drawdown_percent"),
                "daily_dd_breached": daily_dd_breached,
                "daily_dd_breach_date": daily_dd_details.get("breach_date") if daily_dd_breached else None,
            },
        }

        return evaluation

    def transform_mt5_data(self, parsed_data, credential_key=None):
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
        
        evaluation = self._evaluate_account(parsed_data, credential_key)
        
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
            'credentialKey': credential_key,
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
            },
            # Evaluation-related fields (kept within credentials_reports)
            'status': evaluation['status'],
            'isBreached': evaluation['isBreached'],
            'breachReasons': evaluation['breachReasons'],
            'evaluation': evaluation
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
        # Derive credential key from credentialkeys collection using loginId/account
        account_number = parsed_data.get('account', {}).get('account') or parsed_data.get('account')
        credential_key = self._find_credential_key(account_number)

        document = self.transform_mt5_data(parsed_data, credential_key)
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
        Fetch credentials that need to be checked from the credentials collection.
        
        Logic:
        - isActive: false means credential is ASSIGNED and needs to be checked
        - isActive: true means credential is NOT assigned yet (skip)
        - After filtering assigned credentials, check credentials_reports collection
        - Skip credentials that already have status "BREACHED"
        - Only return credentials with status "ACTIVE" or no status (new accounts)
        
        Args:
            server_name: MT5 server name to use for all accounts
            
        Returns:
            List of account dictionaries with login, password, and server
        """
        try:
            # Find all documents in the credentials collection
            credential_docs = list(self.credentials_collection.find())
            
            active_accounts = []
            skipped_breached = 0
            skipped_unassigned = 0
            
            for doc in credential_docs:
                key = doc.get('key', 'Unknown')
                credentials = doc.get('credentials', [])
                
                for cred in credentials:
                    is_active = cred.get('isActive', False)
                    login_id = cred.get('loginId')
                    
                    # Only process ASSIGNED credentials (isActive: false)
                    if is_active:
                        skipped_unassigned += 1
                        continue
                    
                    # Credential is assigned, check if it's already breached in reports
                    try:
                        # Convert loginId to int for lookup
                        account_number = int(login_id) if login_id else None
                        
                        if account_number:
                            # Check credentials_reports collection for existing status
                            report = self.collection.find_one({'account': account_number})
                            
                            if report:
                                status = report.get('status', '')
                                # Skip if already breached
                                if status == self.STATUS_BREACHED:
                                    skipped_breached += 1
                                    continue
                                # Only include if status is ACTIVE
                                if status != self.STATUS_ACTIVE:
                                    continue
                            
                            # Account is either new (no report) or has ACTIVE status
                            account = {
                                'login': account_number,
                                'password': cred['password'],
                                'server': server_name,
                                'key': key,  # Store the key for reference
                                'assignedTo': cred.get('assignedTo'),
                                'assignedOrderId': cred.get('assignedOrderId'),
                                'assignedAt': cred.get('assignedAt')
                            }
                            active_accounts.append(account)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid loginId '{login_id}' for key '{key}': {e}")
                        continue
                    except Exception as e:
                        print(f"Warning: Error checking report for loginId '{login_id}': {e}")
                        continue
            
            print(f"Found {len(active_accounts)} credentials that need checking")
            print(f"  - Skipped {skipped_unassigned} unassigned credentials (isActive: true)")
            print(f"  - Skipped {skipped_breached} already breached credentials")
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
            
            # Build the query (handle numeric or string loginId) and match array element
            login_variants = [str(login_id)]
            try:
                login_variants.append(int(login_id))
            except Exception:
                pass

            query = {"credentials": {"$elemMatch": {"loginId": {"$in": login_variants}}}}
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

