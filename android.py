import subprocess
import os
import re
from logger import logger
from config import settings
from utils import handle_errors, time_it

class AndroidController:
    """Handles Android device automation via ADB."""

    def __init__(self):
        self.adb_path = settings.system.adb_path or "adb"

    def _run_adb(self, command: str) -> str:
        """Helper to run an ADB command."""
        try:
            full_cmd = f"{self.adb_path} {command}"
            result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT)
            return result.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB Error: {e.output.decode('utf-8')}")
            return f"Error: {e.output.decode('utf-8')}"

    @handle_errors("Android")
    def is_connected(self) -> bool:
        """Checks if an Android device is connected."""
        output = self._run_adb("devices")
        lines = output.splitlines()
        # First line is header, subsequent lines should contain "device"
        connected = any("device" in line and not line.startswith("List") for line in lines)
        return connected

    @handle_errors("Android")
    def open_app(self, package_name: str):
        """Opens an app on the phone by its package name."""
        logger.info(f"Opening Android app: {package_name}")
        self._run_adb(f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
        return f"Launched {package_name} on phone."

    @handle_errors("Android")
    def send_sms(self, phone_number: str, message: str):
        """Sends an SMS message via ADB."""
        logger.info(f"Sending SMS to {phone_number}")
        # Escape spaces for ADB
        msg = message.replace(" ", "%s")
        self._run_adb(f"shell am start -a android.intent.action.SENDTO -d sms:{phone_number} --es sms_body {msg} --ez exit_on_sent true")
        self._run_adb("shell input keyevent 22") # Press right
        self._run_adb("shell input keyevent 66") # Press Enter
        return f"Drafted SMS to {phone_number}."

    @handle_errors("Android")
    def read_notifications(self) -> str:
        """Reads recent notifications from the phone."""
        logger.info("Reading phone notifications...")
        output = self._run_adb("shell dumpsys notification --short")
        # Simple extraction of package names and text snippets
        # Dumpsys output is huge, we filter for relevant lines
        lines = output.splitlines()
        relevant = [line.strip() for line in lines if "title=" in line or "text=" in line]
        if not relevant:
            return "No recent notifications found."
        return "\n".join(relevant[:10]) # Return top 10 lines

    @handle_errors("Android")
    def get_battery(self) -> str:
        """Returns the phone's battery level."""
        output = self._run_adb("shell dumpsys battery")
        level_match = re.search(r"level: (\d+)", output)
        if level_match:
            return f"Phone battery is at {level_match.group(1)}%."
        return "Could not read phone battery."

    @handle_errors("Android")
    def take_screenshot(self, filename: str = "phone_screenshot.png"):
        """Takes a screenshot of the phone and pulls it to the computer."""
        remote_path = f"/sdcard/{filename}"
        local_path = os.path.join("logs", filename)
        self._run_adb(f"shell screencap -p {remote_path}")
        self._run_adb(f"pull {remote_path} {local_path}")
        self._run_adb(f"shell rm {remote_path}")
        logger.info(f"Phone screenshot saved to {local_path}")
        return f"Phone screenshot saved to {local_path}."
