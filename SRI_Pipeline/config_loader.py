from dotenv import load_dotenv
import os

class ConfigLoader:
    @staticmethod
    def load_env():
        dotenv_path = os.path.join(os.path.dirname(__file__), 'settings.env')
        load_dotenv(dotenv_path)  # Load environment variables from .env
        return {
            "mqtt": {
                "broker": os.getenv("MQTT_BROKER"),
                "port": int(os.getenv("MQTT_PORT", 1883)),  # Default port is 1883
                "client_id": os.getenv("MQTT_CLIENT_ID"),
            }
        }
