import os
import subprocess
import pyautogui
import keyboard
import pytesseract
import psutil
from PIL import Image
from logger import logger
from config import settings
from utils import handle_errors, time_it

class DesktopController:
    """Handles system-level automation and screen intelligence."""

    def __init__(self):
        # Configure Tesseract path if provided
        if settings.system.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.system.tesseract_cmd
        
        # PyAutoGUI safety settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

    @handle_errors("Desktop")
    def open_app(self, app_name: str):
        """Attempts to open an application by name."""
        logger.info(f"Attempting to open app: {app_name}")
        try:
            # Try to find common paths or use start
            if os.name == 'nt':
                subprocess.Popen(f"start {app_name}", shell=True)
            else:
                subprocess.Popen([app_name])
            return f"Attempted to open {app_name}."
        except Exception:
            # Fallback to searching for the exe in common places could be added here
            return f"Failed to open {app_name} directly. Try saying 'search for {app_name}'."

    @handle_errors("Desktop")
    def type_text(self, text: str):
        """Simulates typing text."""
        logger.info(f"Typing text: {text}")
        pyautogui.write(text, interval=0.01)
        return f"Typed: {text}"

    @handle_errors("Desktop")
    def press_hotkey(self, keys_str: str):
        """Presses a hotkey combination (e.g., 'ctrl', 'c')."""
        keys = [k.strip() for k in keys_str.split('+')]
        logger.info(f"Pressing hotkey: {keys}")
        pyautogui.hotkey(*keys)
        return f"Pressed keys: {keys_str}"

    @handle_errors("Desktop")
    @time_it
    def read_screen(self) -> str:
        """Takes a screenshot and performs OCR to read text."""
        logger.info("Reading screen content...")
        screenshot = pyautogui.screenshot()
        text = pytesseract.image_to_string(screenshot)
        return text if text.strip() else "No readable text found on screen."

    @handle_errors("Desktop")
    def get_system_status(self) -> str:
        """Returns CPU and Memory usage."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        status = f"System Status: CPU at {cpu}%, RAM at {ram}%."
        logger.info(status)
        return status

    @handle_errors("Desktop")
    def take_screenshot(self, filename: str = "screenshot.png"):
        """Takes a screenshot and saves it to the logs directory."""
        path = os.path.join("logs", filename)
        pyautogui.screenshot(path)
        logger.info(f"Screenshot saved to {path}")
        return f"Screenshot captured and saved to {path}."

    @handle_errors("Desktop")
    def set_volume(self, level: int):
        """Sets system volume (0-100)."""
        logger.info(f"Setting volume to {level}%")
        if os.name == 'nt':
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level / 100, None)
        else:
            # Linux/Mac support could be added with amixer/osascript
            return "Volume control only supported on Windows for now."
        return f"Volume set to {level}%."

    @handle_errors("Desktop")
    def set_brightness(self, level: int):
        """Sets screen brightness (0-100)."""
        logger.info(f"Setting brightness to {level}%")
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        return f"Brightness set to {level}%."

    @handle_errors("Desktop")
    def list_windows(self) -> str:
        """Lists all open windows."""
        import pygetwindow as gw
        windows = gw.getAllTitles()
        active = [w for w in windows if w.strip()]
        return "Open Windows: " + ", ".join(active[:10])

    @handle_errors("Desktop")
    def switch_to_window(self, title_part: str):
        """Switches focus to a window containing the title part."""
        import pygetwindow as gw
        try:
            win = gw.getWindowsWithTitle(title_part)[0]
            win.activate()
            return f"Switched to {win.title}."
        except Exception:
            return f"Could not find window with title '{title_part}'."
