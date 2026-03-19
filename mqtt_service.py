import paho.mqtt.client as mqtt

class MQTTService:
    def __init__(self, config, callback):
        self.config = config
        self.callback = callback
        # self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.running = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.config.subscribe_topic)
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        # Trigger the callback which puts it in the Session State queue
        self.callback(payload, self)

    def start(self):
        self.client.connect(self.config.broker, self.config.port, 60)
        self.client.loop_start()
        self.running = True

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.running = False

    def publish(self, topic, payload, retain=False):
        if self.running:
            self.client.publish(topic, payload, retain=retain)