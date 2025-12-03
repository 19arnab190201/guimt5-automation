import json
import re
import sys
from datetime import datetime, timezone


def parse_mt5_report(html_file: str):
    """Parse an MT5 HTML report and print all key metrics."""
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    # === EXTRACT JSON FROM window.__report ===
    match = re.search(r"window\.__report\s*=\s*(\{.*?\})\s*(?:<\/script>|;)", html, re.DOTALL)
    if not match:
        start_idx = html.find("window.__report")
        if start_idx == -1:
            raise ValueError("❌ Could not find 'window.__report' in HTML.")
        json_start = html.find("{", start_idx)
        json_end = html.find("};", json_start)
        json_text = html[json_start:json_end + 1]
    else:
        json_text = match.group(1)

    json_text = json_text.strip()
    if not json_text.endswith("}"):
        json_text = json_text[:json_text.rfind("}") + 1]

    data = json.loads(json_text)

    # === ACCOUNT INFO ===
    acc = data.get("account", {})
    summary = data.get("summary", {})
    balance_data = data.get("balance", {}).get("chart", [])

    name = acc.get("name", "N/A")
    broker = acc.get("broker", "N/A")
    currency = acc.get("currency", "N/A")
    init_balance = float(summary.get("deposit", [0])[0])
    curr_balance = float(data.get("balance", {}).get("balance", 0))
    curr_equity = float(data.get("balance", {}).get("equity", 0))

    print(f"\n📊 ACCOUNT REPORT")
    print("=" * 70)
    print(f"👤 Account: {name}")
    print(f"🏦 Broker : {broker}")
    print(f"💰 Currency: {currency}")
    print(f"💵 Initial Balance: {init_balance:.2f}")
    print(f"📈 Current Balance: {curr_balance:.2f}")
    print(f"📉 Current Equity:  {curr_equity:.2f}")

    # === BALANCE / EQUITY TIMELINE ===
    print("\n📆 Balance & Equity Timeline")
    print("-" * 70)
    print(f"{'UTC Timestamp':<25}{'Balance':<15}{'Equity':<15}")
    for p in balance_data:
        ts = datetime.fromtimestamp(p["x"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        b, e = p["y"][0], p["y"][1]
        print(f"{ts:<25}{b:<15.2f}{e:<15.2f}")

    # === DRAWDOWN ===
    if balance_data:
        lowest_eq_point = min(balance_data, key=lambda x: x["y"][1])
        lowest_eq = lowest_eq_point["y"][1]
        lowest_time = datetime.fromtimestamp(lowest_eq_point["x"], tz=timezone.utc)
        overall_dd = (init_balance - lowest_eq) / init_balance * 100
        threshold = 10

        print("\n📉 DRAWDOWN SUMMARY (Calculated)")
        print("-" * 70)
        print(f"Lowest Equity: {lowest_eq:.2f} ({lowest_time.strftime('%Y-%m-%d %H:%M:%S UTC')})")
        print(f"Overall Drawdown: {overall_dd:.2f}%")
        if overall_dd >= threshold:
            print("🚨 Breach: Over 10% drawdown limit.")
        else:
            print("✅ Within 10% limit.")

    # === GROWTH & DRAWDOWN ===
    if "growth" in data:
        print("\n📈 GROWTH & DRAWDOWN (from MT5 report)")
        print("-" * 70)
        growth_chart = data["growth"]["chart"]
        print(f"{'UTC Timestamp':<25}{'Growth %':<15}{'Drawdown %':<15}")

        for i in range(len(growth_chart[0])):
            ts = datetime.fromtimestamp(growth_chart[0][i]["x"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            g_val = growth_chart[0][i]["y"]
            d_val = growth_chart[1][i]["y"]
            g_val = g_val[0] if isinstance(g_val, list) else g_val
            d_val = d_val[0] if isinstance(d_val, list) else d_val
            growth = float(g_val) * 100
            drawdown = float(d_val) * -100
            print(f"{ts:<25}{growth:<15.2f}{drawdown:<15.2f}")

    # === LONG / SHORT ===
    ind = data.get("longShortIndicators", {})
    totals = data.get("longShortTotal", {})
    long_trades = totals.get("long", 0)
    short_trades = totals.get("short", 0)
    total_trades = long_trades + short_trades
    net_pl = ind.get("netto_pl", [0, 0])
    avg_pl = ind.get("average_pl", [0, 0])
    avg_pl_percent = ind.get("average_pl_percent", [0, 0])
    commissions = ind.get("commissions", [0, 0])
    avg_profit = ind.get("average_profit", [0, 0])
    avg_profit_percent = ind.get("average_profit_percent", [0, 0])
    win_trades = ind.get("win_trades", [0, 0])
    long_ratio = (long_trades / total_trades * 100) if total_trades else 0
    short_ratio = 100 - long_ratio
    long_win_rate = (win_trades[1] / long_trades * 100) if long_trades else 0
    short_win_rate = (win_trades[0] / short_trades * 100) if short_trades else 0

    print("\n📊 LONG / SHORT PERFORMANCE")
    print("-" * 70)
    print(f"Total Trades: {total_trades}")
    print(f"➡️  Long Trades : {long_trades} ({long_ratio:.2f}%)")
    print(f"⬇️  Short Trades: {short_trades} ({short_ratio:.2f}%)")

    print("\n💵 NETTO P/L")
    print(f"Short: {net_pl[0]:.2f}")
    print(f"Long : {net_pl[1]:.2f}")
    print(f"Total: {sum(net_pl):.2f}")

    print("\n✅ Report Parsing Complete.\n")
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse.py <path_to_html_report>")
        sys.exit(1)
    file_path = sys.argv[1]
    parse_mt5_report(file_path)
