import os
import logging
import aiohttp

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleAnalyticsService:
    def __init__(self):
        self.measurement_id = os.getenv("GOOGLE_ANALYTICS_MEASUREMENT_ID")
        self.api_secret = os.getenv("GOOGLE_ANALYTICS_SECRET")
        
        if not self.measurement_id or not self.api_secret:
            self.is_configured = False
            logger.warning("Google Analytics is not configured. Analytics events will not be sent.")
        else:
            self.is_configured = True
            self.endpoint = f"https://www.google-analytics.com/mp/collect?measurement_id={self.measurement_id}&api_secret={self.api_secret}"
            logger.info("Google Analytics service configured.")

    async def log_event(self, user_id: int, event_name: str, params: dict = None):
        """
        Отправляет событие в Google Analytics 4.
        """
        if not self.is_configured:
            logger.info("log_event: analytics is not configured")
            return

        if params is None:
            params = {}

        json_payload = {
            "client_id": str(user_id),
            "events": [{
                "name": event_name,
                "params": params
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, json=json_payload) as response:
                    if response.status >= 300:
                        logger.error(
                            f"Failed to send analytics event. Status: {response.status}, "
                            f"Response: {await response.text()}"
                        )
        except Exception as e:
            logger.error(f"An exception occurred while sending analytics event: {e}")
