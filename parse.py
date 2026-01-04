import json
import re
import sys


def parse_mt5_report(html_file: str):
    """Parse an MT5 HTML report and return parsed data."""
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    # === EXTRACT JSON FROM window.__report ===
    match = re.search(r"window\.__report\s*=\s*(\{.*?\})\s*(?:<\/script>|;)", html, re.DOTALL)
    if not match:
        start_idx = html.find("window.__report")
        if start_idx == -1:
            raise ValueError("Error: Could not find 'window.__report' in HTML.")
        json_start = html.find("{", start_idx)
        json_end = html.find("};", json_start)
        json_text = html[json_start:json_end + 1]
    else:
        json_text = match.group(1)

    json_text = json_text.strip()
    if not json_text.endswith("}"):
        json_text = json_text[:json_text.rfind("}") + 1]

    data = json.loads(json_text)
    return data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse.py <path_to_html_report>")
        sys.exit(1)
    file_path = sys.argv[1]
    parse_mt5_report(file_path)
