import pyautogui
import time
import subprocess
import os
from datetime import datetime
import psutil
import config

# Import configuration
MT5_PATH = config.MT5_PATH
DOWNLOAD_FOLDER = config.DOWNLOAD_FOLDER
REPORT_SAVE_PATH = config.REPORT_SAVE_PATH

# Ensure report directory exists
os.makedirs(REPORT_SAVE_PATH, exist_ok=True)

# PyAutoGUI settings
pyautogui.PAUSE = 1.5
pyautogui.FAILSAFE = True


def is_mt5_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and ('terminal64.exe' in proc.info['name'].lower() or 'terminal.exe' in proc.info['name'].lower()):
            return True
    return False


def close_mt5():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and ('terminal64.exe' in proc.info['name'].lower() or 'terminal.exe' in proc.info['name'].lower()):
            proc.kill()
            time.sleep(2)


def launch_mt5():
    print("Launching MT5...")
    if is_mt5_running():
        print("Existing MT5 detected - closing.")
        close_mt5()

    print("11111111111")
    print("[MT5_PATH]", [MT5_PATH], subprocess.Popen([MT5_PATH]))

    subprocess.Popen([MT5_PATH])
    print("11111111111")

    time.sleep(8)
    print("MT5 launched.")


def login_to_mt5(login, password, server):
    pyautogui.hotkey('shift', 'tab')
    print(f"Logging into MT5 with account {login}...")
    pyautogui.hotkey('alt', 'f')
    time.sleep(1)
    pyautogui.press('l')
    time.sleep(2)

    # Login ID
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.write(str(login), interval=0.1)
    pyautogui.press('tab')

    # Password
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.write(password, interval=0.1)
    pyautogui.press('tab')

    # Server
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.write(server, interval=0.1)
    pyautogui.press('enter')
    time.sleep(6)
    print("Login complete.")


def generate_report():
    """Generate report via Alt+E path"""
    print("Generating report via Alt+E...")
    pyautogui.hotkey('alt', 'e')
    time.sleep(2)
    pyautogui.press('r')
    time.sleep(2)
    print("Report dialog opened (user/browser will open shortly).")


def save_report(login):
    """Saves report once it opens in browser"""
    print("Saving report...")
    time.sleep(5)
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"MT5_Report_{login}_{timestamp}"
    pyautogui.write(filename)
    pyautogui.press('enter')
    time.sleep(3)

    full_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.html")
    print(f"Report saved: {full_path}")
    return full_path


def automate_mt5_report(login, password, server):
    """Main wrapper function to automate MT5 report generation for a single account"""
    print("=" * 70)
    print(f"MT5 REPORT AUTOMATION STARTED for account {login}")
    print("=" * 70)

    try:
        launch_mt5()
        login_to_mt5(login, password, server)
        generate_report()
        report_path = save_report(login)

        print("Automation complete.")
        return report_path

    except Exception as e:
        print(f"Error: Automation failed: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    TEST_LOGIN = 279288123
    TEST_PASSWORD = "56Dh@466"
    TEST_SERVER = "Exness-MT5Trial8"
    automate_mt5_report(TEST_LOGIN, TEST_PASSWORD, TEST_SERVER)
