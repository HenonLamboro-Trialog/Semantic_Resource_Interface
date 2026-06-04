class AppConfig:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.subscribe_topic = "resources/raw"
        self.publish_topic = "resources/semantic"
        self.base_uri = "http://w3id.org/resonance/resource/"
        self.ontology_uri = "https://w3id.org/resonance/SRI4ALL#"