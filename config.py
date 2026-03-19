from dataclasses import dataclass

@dataclass
class AppConfig:
    broker: str = "localhost"
    port: int = 1883
    subscribe_topic: str = "resources/raw"
    publish_topic: str = "resources/semantic"
    base_uri: str = "http://w3id.org/resonance/resource/"
    ontology_uri: str = "https://w3id.org/resonance/SRI4ALL#"