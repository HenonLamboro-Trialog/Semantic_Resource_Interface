from rdflib import Graph, Namespace, Literal, URIRef
from typing import Dict, Any

class SemanticInterface:
    def __init__(self, mqtt_client, rdf_converter):
        self.mqtt_client = mqtt_client
        self.rdf_converter = rdf_converter
        self.topics = {
            'ev': 'ev',
            'pv': 'pv',
            'hvac': 'hvac',
            'building': 'building',
            'weather': 'weather'
        }
        
    def start(self):
        self.mqtt_client.connect()
        
    def stop(self):
        self.mqtt_client.disconnect()
        
    def process_input(self, data_type: str, data: Dict[str, Any]):
        if data_type not in self.topics:
            raise ValueError(f"Invalid data type: {data_type}")
            
        # Convert data to RDF
        rdf_data = self.rdf_converter.convert_to_rdf(self.topics[data_type], data)
        
        # Publish to semantic topics
        topic = self.topics[data_type]
        # self.mqtt_client.publish(topic, json.dumps(data))
        if data_type == 'pv':
            new_topic = 'resonance/sri/partner1/site1/pv'
            self.mqtt_client.publish(new_topic, rdf_data)

        elif data_type == 'building':
            new_topic = 'resonance/sri/partner2/site1/building'
            self.mqtt_client.publish(new_topic, rdf_data)

        else:
            self.mqtt_client.publish(f"resonance/sri/{topic}", rdf_data)