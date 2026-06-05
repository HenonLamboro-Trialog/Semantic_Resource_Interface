import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect("127.0.0.1", 1883, 60)

client.loop_start()

# data = [{
#     "resource_id": "sensor_002",
#     "type": "TemperatureSensor",
#     "value": 90,
#     "unit": "Fahrenheit",
#     "timestamp": "2026-02-24T10:30:00"}
#  , {
#     "resource_id": "sensor_003",
#     "type": "TemperatureSensor",
#     "value": 23.5,
#     "unit": "Celsius",
#     "timestamp": "2026-02-24T10:30:00"
#  }]

data = {
  "resource_id":"01",
  "source":"init",
  "output":"true",
  "apower":8.6,
  "voltage":231.7,
  "current":0.088,
  "aenergy":{"total":13652.762},
  "temperature":{"tC":56.3, "tF":133.4}
}

result = client.publish("resources/raw", json.dumps(data))

result.wait_for_publish()   # ensures it is actually sent

time.sleep(0.5)

client.loop_stop()
client.disconnect()