from rdflib import Graph, Namespace, Literal, URIRef, RDF
from rdflib.namespace import XSD
from datetime import datetime
from typing import Any, Dict
import urllib.parse

class RDFConverter:
    def __init__(self):
        # Define namespaces
        self.SAREF = Namespace("https://saref.etsi.org/core/")
        self.SAREF4ENER = Namespace("https://saref.etsi.org/saref4ener/")
        self.SRI4BUILDING = Namespace("https://w3id.org/resonance/sri4building#")
        self.SRI4WEATHER = Namespace("https://w3id.org/resonance/sri4weather##")
        self.SRI4EV = Namespace("https://w3id.org/resonance/sri4ev#")
        self.SRI4PV = Namespace("https://w3id.org/resonance/sri4pv#")
        self.SRI4ALL = Namespace("https://w3id.org/resonance/sri4all#")
        self.graph = Graph()

        # Bind namespaces
        self.graph.bind("saref", self.SAREF)
        self.graph.bind("saref4ener", self.SAREF4ENER)
        self.graph.bind("sri4building", self.SRI4BUILDING)
        self.graph.bind("sri4weather", self.SRI4WEATHER)
        self.graph.bind("sri4ev", self.SRI4EV)
        self.graph.bind("sri4pv", self.SRI4PV)
        self.graph.bind("sri4all", self.SRI4ALL)

    def convert_to_rdf(self, topic: str, data: Any) -> str:
        # Convert data to RDF based on the topic
        if topic == 'pv':
            self._process_pv_production(data)
        elif topic == 'building':
            self._process_building_data(data)
        else:
            raise ValueError(f"Unsupported topic: {topic}")
        
        return self.graph.serialize(format="turtle")

    def _process_pv_production(self, data: Dict[str, Any]):
        # Process PV production JSON data
        measurements = data.get("powerMeasurements", [])
        for i, measurement in enumerate(measurements):
            timestamp = measurement.get("timestamp")
            value = measurement.get("value")
            unit = measurement.get("unit", "Watt")
            commodity_quantity = measurement.get("commodityQuantity", "")

            # Generate URI for measurement
            measurement_uri = URIRef(f"https://w3id.org/resonance/pv/measurement/{i + 1}")
            
            # Add triples
            self.graph.add((measurement_uri, RDF.type, self.SRI4ALL.PowerMeasurement))
            self.graph.add((measurement_uri, self.SRI4PV.isAbout, self.SRI4PV.Photovoltaic))
            self.graph.add((measurement_uri, self.SRI4ALL.powerValue, Literal(value, datatype=XSD.float)))
            self.graph.add((measurement_uri, self.SRI4ALL.isMeasuredIn, Literal(unit)))
            self.graph.add((measurement_uri, self.SAREF4ENER.CommodityQuantity, Literal(commodity_quantity)))
            self.graph.add((measurement_uri, self.SRI4PV.timestamp, Literal(timestamp, datatype=XSD.dateTime)))

    def _process_building_data(self, data: Any):
        # Process building data from CSV."""
        if isinstance(data, list):  # Data is a list of rows
            for i, row in enumerate(data):
                timestamp = datetime.strptime(row['timestamp'], "%d/%m/%Y %H:%M").isoformat()
                for key, value in row.items():
                    if key != "timestamp":
                        encoded_key = urllib.parse.quote(key)
                        measurement_uri = URIRef(f"https://w3id.org/resonance/building/measurement/{encoded_key}/{i + 1}")
                        rdf_type = self._get_building_property_type(key)
                        
                        # Add triples
                        self.graph.add((measurement_uri, RDF.type, rdf_type))
                        self.graph.add((measurement_uri, self.SRI4BUILDING.value, Literal(float(value), datatype=XSD.float)))
                        self.graph.add((measurement_uri, self.SRI4BUILDING.timeStamp, Literal(timestamp, datatype=XSD.dateTime)))

    def _get_building_property_type(self, key: str) -> URIRef:
        """Map building data keys to RDF types."""
        mapping = {
            "Electricity_consumption": self.SRI4BUILDING.EnergyConsumption,
            "District_heating_consumption": self.SRI4BUILDING.HeatConsumption,
            "Outdoor_temperature": self.SRI4BUILDING.OutdoorTemperature,
            "Indoor_temperature_measurement_point_1": self.SRI4BUILDING.IndoorTemperature,
            "Indoor_temperature_measurement_point_2": self.SRI4BUILDING.IndoorTemperature,
            "Indoor_temperature_measurement_point_3": self.SRI4BUILDING.IndoorTemperature,
            "Indoor_temperature_mean_value": self.SRI4BUILDING.IndoorTemperatureMean
        }
        return mapping.get(key, self.SRI4BUILDING.UnknownMeasurement)
