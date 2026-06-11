"""End-to-end: meter snapshot -> conformant YAML -> RDF, plus a linter gate.

Ties together the source adapter, the conformant mapping, the generic mapper,
and the ontology linter against the real RESONANCE-Ontology TTLs.
"""

import os

import yaml
from rdflib import Graph, Namespace, Literal, RDF
from rdflib.namespace import XSD

from semantic_mapper import semanticise_data
from tools.mapping_linter import (
    load_ontology_terms, ontology_ttls, lint_mapping,
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ONTOLOGY_DIR = os.path.normpath(os.path.join(REPO, "..", "RESONANCE-Ontology"))
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
}


def _mapping():
    with open(MAPPING_PATH) as f:
        return yaml.safe_load(f)


def test_meter_mapping_is_ontology_conformant():
    known = load_ontology_terms(ontology_ttls(ONTOLOGY_DIR))
    assert lint_mapping(_mapping(), known) == []


def test_snapshot_serializes_to_conformant_power_measurement():
    g = Graph()
    g.parse(data=semanticise_data([SNAPSHOT], _mapping(), BASE), format="turtle")

    device = next(iter(g.subjects(SRI.measuresPower, None)))
    pm = next(iter(g.objects(device, SRI.measuresPower)))

    assert (pm, SRI.powerValue, Literal(-4834.9, datatype=XSD.float)) in g
    assert (pm, SRI.isMeasuredIn, UNIT.W) in g
    assert (pm, SRI.timestamp,
            Literal("2026-06-10T13:15:00", datatype=XSD.dateTime)) in g
    # power property node typed ActivePower, linked via hasPowerProperty
    prop = next(iter(g.objects(pm, SRI.hasPowerProperty)))
    assert (prop, RDF.type, SRI.ActivePower) in g
