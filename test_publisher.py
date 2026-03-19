import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

client.loop_start()

data = {
    "resource_id": "sensor_002",
    "type": "TemperatureSensor",
    "value": 23.5,
    "unit": "Celsius",
    "timestamp": "2026-02-24T10:30:00"
}

result = client.publish("resources/raw", json.dumps(data))

result.wait_for_publish()   # ensures it is actually sent

time.sleep(0.5)

client.loop_stop()
client.disconnect()