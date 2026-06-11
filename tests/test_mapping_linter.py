"""Tests for the YAML-mapping ontology-conformance linter.

The linter answers: does every ontology term a mapping references actually
exist in the RESONANCE reference ontology? Terms in namespaces we have no
ontology for (xsd, qudt units) are skipped, not flagged.
"""

import textwrap

from tools.mapping_linter import (
    load_ontology_terms,
    referenced_terms,
    lint_mapping,
)

KNOWN = {
    "https://w3id.org/resonance/SRI4ALL#PowerMeasurement",
    "https://w3id.org/resonance/SRI4ALL#consistsOfPowerMeasurement",
    "https://w3id.org/resonance/SRI4ALL#powerValue",
    "https://saref.etsi.org/core/Sensor",
}

MAPPING = {
    "prefixes": {
        "sri4all": "https://w3id.org/resonance/SRI4ALL#",
        "saref": "https://saref.etsi.org/core/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    },
    "resource": {"id_path": "resource_id",
                 "class": {"prefix": "saref", "name": "Sensor"}},
    "measurements": [
        {
            "path": "apower",
            "class": {"prefix": "sri4all", "name": "PowerMeasurement"},
            "relation": {"prefix": "sri4all", "name": "consistsOfPowerMeasurement"},
            "value_predicate": {"prefix": "sri4all", "name": "powerValue"},
        }
    ],
}


def test_referenced_terms_resolves_prefixes_to_full_uris():
    refs = referenced_terms(MAPPING)
    uris = {r["uri"] for r in refs}
    assert "https://w3id.org/resonance/SRI4ALL#PowerMeasurement" in uris
    assert "https://w3id.org/resonance/SRI4ALL#consistsOfPowerMeasurement" in uris
    assert "https://w3id.org/resonance/SRI4ALL#powerValue" in uris
    assert "https://saref.etsi.org/core/Sensor" in uris


def test_conformant_mapping_has_no_issues():
    assert lint_mapping(MAPPING, KNOWN) == []


def test_undefined_resonance_term_is_flagged():
    bad = {
        "prefixes": {"sri4all": "https://w3id.org/resonance/SRI4ALL#"},
        "resource": {"id_path": "id",
                     "class": {"prefix": "sri4all", "name": "Sensor"}},
        "measurements": [
            {"path": "v",
             "class": {"prefix": "sri4all", "name": "EnergyMeasurement"},
             "relation": {"prefix": "sri4all", "name": "hasEnergyMeasurement"}},
        ],
    }
    issues = lint_mapping(bad, KNOWN)
    flagged = {i["term"] for i in issues}
    assert "https://w3id.org/resonance/SRI4ALL#EnergyMeasurement" in flagged
    assert "https://w3id.org/resonance/SRI4ALL#hasEnergyMeasurement" in flagged


def test_terms_in_unmodelled_namespace_are_not_flagged():
    # xsd / qudt unit terms are not part of the resonance ontology -> skip.
    m = {
        "prefixes": {"unit": "http://qudt.org/vocab/unit/",
                     "sri4all": "https://w3id.org/resonance/SRI4ALL#"},
        "resource": {"id_path": "id",
                     "class": {"prefix": "sri4all", "name": "PowerMeasurement"}},
        "properties": [
            {"path": "u", "predicate": {"prefix": "unit", "name": "KiloW"}},
        ],
    }
    issues = lint_mapping(m, KNOWN)
    assert all("qudt.org" not in i["term"] for i in issues)


def test_load_ontology_terms_reads_defined_subjects(tmp_path):
    ttl = tmp_path / "mini.ttl"
    ttl.write_text(textwrap.dedent("""
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix sri4all: <https://w3id.org/resonance/SRI4ALL#> .
        sri4all:PowerMeasurement rdf:type owl:Class .
        sri4all:powerValue rdf:type owl:DatatypeProperty .
    """))

    terms = load_ontology_terms([str(ttl)])

    assert "https://w3id.org/resonance/SRI4ALL#PowerMeasurement" in terms
    assert "https://w3id.org/resonance/SRI4ALL#powerValue" in terms
