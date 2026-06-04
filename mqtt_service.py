import paho.mqtt.client as mqtt
import threading


class MQTTService:
    def __init__(self, config, on_message_callback):
        self.config = config
        self.on_message_callback = on_message_callback
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.running = False
        self.thread = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            client.subscribe(
                self.config.subscribe_topic)
            print(
                f"Subscribed to: "
                f"{self.config.subscribe_topic}")
        else:
            print(
                f"MQTT connection failed "
                f"with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            print(
                f"Received message on "
                f"{msg.topic}: {payload}" )
            self.on_message_callback(
                payload,
                self )
        except Exception as e:
            print(f"Message processing error: {e}")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
    def start(self):
        if self.running:
            return
        self.client.connect(
            self.config.broker,
            int(self.config.port),
            60)
        self.running = True
        self.thread = threading.Thread(
            target=self.client.loop_forever,
            daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print(f"Error stopping MQTT: {e}")
    def publish(self, topic, payload):
        try:
            result = self.client.publish(
                topic,
                payload)
            status = result[0]
            if status == 0:
                print(f"Published to {topic}")
            else:
                print(f"Failed to publish to {topic}" )
        except Exception as e:
            print(f"Publish error: {e}")