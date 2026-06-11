"""End-to-end: meter snapshot -> diagram-vocabulary YAML -> RDF.

Vocabulary follows the RESONANCE-Ontology diagram (the current source of truth):
sri4all:value / sri4all:timeStamp / sri4all:hasUnitOfMeasurment and the
hasPowerMeasurement / hasMeasurement / hasEnergyMeasurement relations.
"""

import os

import yaml
from rdflib import Graph, Namespace, Literal, RDF
from rdflib.namespace import XSD

from semantic_mapper import semanticise_data

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MAPPING_PATH = os.path.join(REPO, "Mappings", "raiprogramming_meter.yaml")

SRI = Namespace("https://w3id.org/resonance/SRI4ALL#")
UNIT = Namespace("http://qudt.org/vocab/unit/")
BASE = "http://w3id.org/resonance/resource/"

# Shape produced by adapters.raiprogramming.source.device_snapshot
SNAPSHOT = {
    "resource_id": "HEMS1_21",
    "device_type": "EE_METER_ISKRA_AM550",
    "timestamp": "2026-06-10T13:15:00",
    "active_power": {"value": -4834.9, "unit": "W"},
    "reactive_power": {"value": 12.0, "unit": "VAr"},
    "voltage_l1": {"value": 231.7, "unit": "V"},
    "current_l1": {"value": 0.088, "unit": "A"},
    "import_active_energy": {"value": 13652.7, "unit": "Wh"},
    "frequency": {"value": 50.01, "unit": "Hertz"},
}


def _graph():
    with open(MAPPING_PATH) as f:
        mapping = yaml.safe_load(f)
    g = Graph()
    g.parse(data=semanticise_data([SNAPSHOT], mapping, BASE), format="turtle")
    return g


def test_meter_device_is_a_power_device():
    g = _graph()
    assert (None, RDF.type, SRI.PowerDevice) in g


def test_active_power_uses_diagram_vocabulary():
    g = _graph()
    device = next(iter(g.subjects(RDF.type, SRI.PowerDevice)))
    pms = list(g.objects(device, SRI.hasPowerMeasurement))
    # active power measurement, identified by its value
    pm = next(p for p in pms
              if (p, SRI.value, Literal(-4834.9, datatype=XSD.float)) in g)
    assert (pm, RDF.type, SRI.PowerMeasurement) in g
    assert (pm, SRI.hasUnitOfMeasurment, UNIT.W) in g
    assert (pm, SRI.timeStamp,
            Literal("2026-06-10T13:15:00", datatype=XSD.dateTime)) in g
    prop = next(iter(g.objects(pm, SRI.hasPowerProperty)))
    assert (prop, RDF.type, SRI.ActivePower) in g


def test_voltage_current_and_energy_are_emitted():
    g = _graph()
    assert (None, RDF.type, SRI.Voltage) in g
    assert (None, RDF.type, SRI.Current) in g
    assert (None, RDF.type, SRI.EnergyMeasurement) in g
    # voltage value carried through
    v = next(iter(g.subjects(RDF.type, SRI.Voltage)))
    assert (v, SRI.value, Literal(231.7, datatype=XSD.float)) in g


def test_frequency_is_emitted():
    g = _graph()
    f = next(iter(g.subjects(RDF.type, SRI.Frequency)))
    assert (f, SRI.value, Literal(50.01, datatype=XSD.float)) in g
    assert (f, SRI.hasUnitOfMeasurment, UNIT.Hertz) in g
