import httpx
import os
from logger import logger
from config import settings
from utils import handle_errors, time_it
from typing import List, Dict, Any, Optional

class SmartHomeController:
    """Handles interaction with Home Assistant via REST API."""

    def __init__(self):
        self.url = os.getenv("HASS_URL")
        self.token = os.getenv("HASS_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

    @handle_errors("SmartHome")
    def is_available(self) -> bool:
        """Checks if Home Assistant is reachable."""
        if not self.url or not self.token:
            return False
        return True

    @handle_errors("SmartHome")
    @time_it
    async def get_states(self) -> List[Dict[str, Any]]:
        """Returns all entity states from Home Assistant."""
        if not self.is_available(): return []
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/api/states", headers=self.headers)
            response.raise_for_status()
            return response.json()

    @handle_errors("SmartHome")
    async def call_service(self, domain: str, service: str, entity_id: str, data: Optional[Dict[str, Any]] = None):
        """Calls a Home Assistant service (e.g., light.turn_on)."""
        if not self.is_available(): return "Home Assistant credentials missing."
        
        payload = data or {}
        payload["entity_id"] = entity_id
        
        logger.info(f"Calling HASS service: {domain}.{service} for {entity_id}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return f"Service {domain}.{service} executed successfully."

    @handle_errors("SmartHome")
    async def get_entity_status(self, entity_id: str) -> str:
        """Returns the current state of a specific entity."""
        if not self.is_available(): return "Home Assistant offline."
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.url}/api/states/{entity_id}", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return f"The state of {entity_id} is {data['state']}."
