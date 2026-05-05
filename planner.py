import datetime
from typing import List, Dict, Any, Callable, Optional
from logger import logger
from utils import handle_errors
from memory import Memory
from desktop import DesktopController
from android import AndroidController
from web import WebIntelligence
from smarthome import SmartHomeController

class Planner:
    """Handles task decomposition and tool execution across all layers."""

    def __init__(self, memory: Optional[Memory] = None):
        self.tools: Dict[str, Callable] = {}
        self.memory = memory or Memory()
        self.desktop = DesktopController()
        self.android = AndroidController()
        self.web = WebIntelligence()
        self.home = SmartHomeController()
        self._register_default_tools()

    def _register_default_tools(self):
        """Registers all tools from Desktop, Android, Web, and Smart Home."""
        # System
        self.register_tool("get_time", self.get_time)
        self.register_tool("get_date", self.get_date)
        
        # Desktop (Laptop)
        self.register_tool("open_app", self.desktop.open_app)
        self.register_tool("type_text", self.desktop.type_text)
        self.register_tool("press_hotkey", self.desktop.press_hotkey)
        self.register_tool("read_screen", self.desktop.read_screen)
        self.register_tool("take_screenshot", self.desktop.take_screenshot)
        self.register_tool("get_system_status", self.desktop.get_system_status)
        self.register_tool("set_volume", self.desktop.set_volume)
        self.register_tool("set_brightness", self.desktop.set_brightness)
        self.register_tool("list_windows", self.desktop.list_windows)
        self.register_tool("switch_to_window", self.desktop.switch_to_window)
        
        # Android (Phone)
        self.register_tool("phone_open_app", self.android.open_app)
        self.register_tool("phone_send_sms", self.android.send_sms)
        self.register_tool("phone_read_notifications", self.android.read_notifications)
        self.register_tool("phone_get_battery", self.android.get_battery)
        
        # Web
        self.register_tool("web_search", self.web.search)
        self.register_tool("web_scrape", self.web.scrape_url)
        self.register_tool("web_get_news", self.web.get_news)
        self.register_tool("web_search_images", self.web.search_images)
        
        # Smart Home
        self.register_tool("home_control", self.home.call_service)
        self.register_tool("home_status", self.home.get_entity_status)

        # Memory
        self.register_tool("remember_preference", self.remember_preference)
        self.register_tool("search_memory", self.search_memory)

        # Phone Extras
        self.register_tool("phone_screenshot", self.android.take_screenshot)

    def register_tool(self, name: str, func: Callable):
        self.tools[name] = func

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [
            {"name": "get_time", "description": "Returns current time.", "parameters": {"type": "object", "properties": {}}},
            {"name": "get_date", "description": "Returns today's date.", "parameters": {"type": "object", "properties": {}}},
            
            {"name": "open_app", "description": "Open a laptop app.", "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}}},
            {"name": "type_text", "description": "Type text on computer.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}}},
            {"name": "press_hotkey", "description": "Press a hotkey (e.g. ctrl+c).", "parameters": {"type": "object", "properties": {"keys_str": {"type": "string"}}}},
            {"name": "read_screen", "description": "Read text on screen using OCR.", "parameters": {"type": "object", "properties": {}}},
            {"name": "take_screenshot", "description": "Capture a screenshot and save it locally.", "parameters": {"type": "object", "properties": {"filename": {"type": "string", "description": "Name of the file (e.g. screen.png)"}}}},
            {"name": "get_system_status", "description": "Get CPU and RAM usage.", "parameters": {"type": "object", "properties": {}}},
            {"name": "set_volume", "description": "Set computer volume (0-100).", "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}}},
            {"name": "set_brightness", "description": "Set screen brightness (0-100).", "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}}},
            {"name": "list_windows", "description": "List all open window titles.", "parameters": {"type": "object", "properties": {}}},
            {"name": "switch_to_window", "description": "Focus a window by title.", "parameters": {"type": "object", "properties": {"title_part": {"type": "string"}}}},
            
            {"name": "phone_open_app", "description": "Open app on phone by package name.", "parameters": {"type": "object", "properties": {"package_name": {"type": "string"}}}},
            {"name": "phone_send_sms", "description": "Send SMS from phone.", "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}, "message": {"type": "string"}}}},
            {"name": "phone_read_notifications", "description": "Read recent phone notifications.", "parameters": {"type": "object", "properties": {}}},
            {"name": "phone_get_battery", "description": "Check phone battery level.", "parameters": {"type": "object", "properties": {}}},
            
            {"name": "web_search", "description": "Search the internet for information.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}},
            {"name": "web_scrape", "description": "Extract readable text from a website URL.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}}},
            {"name": "web_get_news", "description": "Get latest news on a specific topic.", "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}}},
            {"name": "web_search_images", "description": "Search for images on the web.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}},
            
            {
                "name": "home_control", 
                "description": "Control a smart home device via Home Assistant.", 
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "domain": {"type": "string", "description": "e.g. light, switch"},
                        "service": {"type": "string", "description": "e.g. turn_on, turn_off"},
                        "entity_id": {"type": "string", "description": "e.g. light.living_room"}
                    },
                    "required": ["domain", "service", "entity_id"]
                }
            },
            {"name": "home_status", "description": "Get status of a smart home entity.", "parameters": {"type": "object", "properties": {"entity_id": {"type": "string"}}}},
            
            {"name": "remember_preference", "description": "Save a user preference (e.g. favorite color, name).", "parameters": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}}},
            {"name": "search_memory", "description": "Search through past interactions and preferences.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}},
            {"name": "phone_screenshot", "description": "Capture a screenshot of the connected Android phone.", "parameters": {"type": "object", "properties": {"filename": {"type": "string", "description": "Optional filename."}}}}
        ]

    @handle_errors("Planner")
    async def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        if name in self.tools:
            import asyncio
            if asyncio.iscoroutinefunction(self.tools[name]):
                result = await self.tools[name](**args)
            else:
                result = self.tools[name](**args)
            return str(result)
        return f"Error: Tool '{name}' not found."

    def get_time(self) -> str: return datetime.datetime.now().strftime("%I:%M %p")
    def get_date(self) -> str: return datetime.datetime.now().strftime("%A, %B %d, %Y")
    def remember_preference(self, key: str, value: str) -> str:
        self.memory.add_preference(key, value)
        return f"Saved your {key} preference."
    def search_memory(self, query: str) -> str:
        results = self.memory.search(query)
        return "\n".join(results) if results else "Nothing found."
