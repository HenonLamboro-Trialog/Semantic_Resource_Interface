"""semantic_mapper: unit/timestamp predicates must be overridable per measurement.

The ontology uses sri4all:isMeasuredIn (unit) and sri4all:timestamp, but the
mapper hard-codes sri4all:hasUnitOfMeasurment and sri4all:timeStamp. To emit
ontology-conformant RDF the mapping must be able to override those predicates,
without breaking the existing default behaviour.
"""

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import XSD

from semantic_mapper import semanticise_data

SRI = Namespace("https://w3id.org/resonance/SRI4ALL#")
UNIT = Namespace("http://qudt.org/vocab/unit/")
BASE = "http://w3id.org/resonance/resource/"

DATA = {"resource_id": "m1", "timestamp": "2026-06-10T13:15:00",
        "active_power": {"value": -4834.9, "unit": "KiloW"}}


def _graph(mapping):
    g = Graph()
    g.parse(data=semanticise_data([DATA], mapping, BASE), format="turtle")
    return g


def _conformant_mapping():
    return {
        "prefixes": {"sri4all": str(SRI), "unit": str(UNIT),
                     "xsd": str(XSD)},
        "resource": {"id_path": "resource_id",
                     "class": {"prefix": "sri4all", "name": "PowerDevice"}},
        "measurements": [{
            "path": "active_power.value",
            "class": {"prefix": "sri4all", "name": "PowerMeasurement"},
            "relation": {"prefix": "sri4all", "name": "consistsOfPowerMeasurement"},
            "value_predicate": {"prefix": "sri4all", "name": "powerValue"},
            "datatype": "float",
            "unit_path": "active_power.unit", "unit_prefix": "unit",
            "unit_predicate": {"prefix": "sri4all", "name": "isMeasuredIn"},
            "timestamp_path": "timestamp", "timestamp_datatype": "dateTime",
            "timestamp_predicate": {"prefix": "sri4all", "name": "timestamp"},
        }],
    }


def test_unit_predicate_override_emits_isMeasuredIn():
    g = _graph(_conformant_mapping())
    pm = next(iter(g.subjects(predicate=SRI.powerValue)))
    assert (pm, SRI.isMeasuredIn, UNIT.KiloW) in g
    # the hard-coded default must NOT appear
    assert not list(g.objects(pm, SRI.hasUnitOfMeasurment))


def test_timestamp_predicate_override_emits_sri4all_timestamp():
    g = _graph(_conformant_mapping())
    pm = next(iter(g.subjects(predicate=SRI.powerValue)))
    assert (pm, SRI.timestamp,
            Literal("2026-06-10T13:15:00", datatype=XSD.dateTime)) in g
    assert not list(g.objects(pm, SRI.timeStamp))


def test_defaults_unchanged_when_no_override():
    m = _conformant_mapping()
    meas = m["measurements"][0]
    del meas["unit_predicate"]
    del meas["timestamp_predicate"]
    g = _graph(m)
    pm = next(iter(g.subjects(predicate=SRI.powerValue)))
    # legacy behaviour preserved
    assert (pm, SRI.hasUnitOfMeasurment, UNIT.KiloW) in g
    assert list(g.objects(pm, SRI.timeStamp))
