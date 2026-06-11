import paho.mqtt.client as mqtt
import json
import time

class MQTTClient:
    def __init__(self, config):
        self.config = config
        self.client = mqtt.Client(client_id=config['client_id'])
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.callbacks = {}
        
    def connect(self):
        self.client.connect(self.config['broker'], self.config['port'])
        self.client.loop_start()
        
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        
    def subscribe(self, topic):
        self.client.subscribe(topic)
        
    def publish(self, topic, payload):
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        self.client.publish(topic, payload)
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Connection failed with code {rc}")
            
    def _on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            if message.topic in self.callbacks:
                self.callbacks[message.topic](message.topic, payload)
        except json.JSONDecodeError:
            print(f"Error decoding message on topic {message.topic}")