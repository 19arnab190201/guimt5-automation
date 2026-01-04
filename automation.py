import pyautogui
import time
import subprocess
import os
from datetime import datetime
import psutil
import config
import logging

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


def get_logger():
    """Get the logger instance"""
    return logging.getLogger('MT5Automation')


def focus_mt5_window():
    """Click on top-left of screen to ensure MT5 window is in focus"""
    # Click on top-left area of the screen (title bar region)
    # MT5 typically opens maximized or at top-left
    pyautogui.click(100, 15)
    get_logger().info("Clicked on title bar to focus MT5 window")


def launch_mt5():
    logger = get_logger()
    logger.info("Launching MT5...")
    if is_mt5_running():
        logger.info("Existing MT5 detected - closing.")
        close_mt5()

    subprocess.Popen([MT5_PATH])

    time.sleep(8)
    
    # Focus the MT5 window by clicking on title bar
    focus_mt5_window()
    time.sleep(1)
    
    logger.info("MT5 launched and focused.")


def login_to_mt5(login, password, server):
    logger = get_logger()
    # Temporarily reduce pause for faster input
    original_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0.1  # Much faster for input operations
    
    try:
        pyautogui.hotkey('shift', 'tab')
        logger.info(f"Logging into MT5 with account {login}...")
        pyautogui.hotkey('alt', 'f')
        time.sleep(0.3)  # Reduced from 1 second

        # Login ID - faster typing
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        pyautogui.write(str(login), interval=0.01)  # Much faster typing
        pyautogui.press('tab')
        time.sleep(0.1)  # Small delay for field to process

        # Password - faster typing
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        pyautogui.write(password, interval=0.01)  # Much faster typing
        pyautogui.press('tab')
        time.sleep(0.1)  # Small delay for field to process

        # Server - faster typing
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        pyautogui.write(server, interval=0.01)  # Much faster typing
        pyautogui.press('enter')
        time.sleep(3)  # Reduced from 6 seconds - enough for login to process
        logger.info("Login complete.")
    finally:
        # Restore original pause setting
        pyautogui.PAUSE = original_pause


def generate_report():
    """Generate report via Alt+E path"""
    logger = get_logger()
    logger.info("Generating report via Alt+E...")
    pyautogui.hotkey('alt', 'e')
    time.sleep(2)
    pyautogui.press('r')
    time.sleep(2)
    logger.info("Report dialog opened (user/browser will open shortly).")


def save_report(login):
    """Saves report once it opens in browser"""
    logger = get_logger()
    logger.info("Saving report...")
    time.sleep(5)
    pyautogui.hotkey('ctrl', 's')
    time.sleep(2)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"MT5_Report_{login}_{timestamp}"
    pyautogui.write(filename)
    pyautogui.press('enter')
    time.sleep(3)

    full_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.html")
    logger.info(f"Report saved: {full_path}")
    return full_path


def automate_mt5_report(login, password, server):
    """Main wrapper function to automate MT5 report generation for a single account"""
    logger = get_logger()
    logger.info("=" * 70)
    logger.info(f"MT5 REPORT AUTOMATION STARTED for account {login}")
    logger.info("=" * 70)

    try:
        launch_mt5()
        login_to_mt5(login, password, server)
        generate_report()
        report_path = save_report(login)

        logger.info("Automation complete.")
        return report_path

    except Exception as e:
        logger.error(f"ERROR: Automation failed: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    TEST_LOGIN = 279288123
    TEST_PASSWORD = "56Dh@466"
    TEST_SERVER = "Exness-MT5Trial8"
    automate_mt5_report(TEST_LOGIN, TEST_PASSWORD, TEST_SERVER)
