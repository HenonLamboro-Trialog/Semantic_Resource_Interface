"""Ontology-conformance linter for YAML mapping files.

Checks that every ontology term a mapping references (resource/measurement
classes, relations, value predicates, linked properties) is actually defined
in the RESONANCE reference ontology. Terms whose namespace is not part of the
loaded ontology (e.g. xsd, qudt units) are skipped rather than flagged, so the
linter only reports genuine "you used a term that doesn't exist" problems.

Usage (CLI):
    python -m tools.mapping_linter Mappings/power_sensor.yaml \\
        --ontology ../RESONANCE-Ontology
"""

import argparse
import glob
import os
import sys

import yaml
from rdflib import Graph, RDF, URIRef


# --- ontology side ---------------------------------------------------------

def load_ontology_terms(ttl_paths):
    """Return the set of defined term URIs (any subject with an rdf:type)."""
    terms = set()
    for path in ttl_paths:
        g = Graph()
        g.parse(path, format="turtle")
        for subject in set(g.subjects(RDF.type, None)):
            if isinstance(subject, URIRef):
                terms.add(str(subject))
    return terms


def ontology_ttls(ontology_dir):
    """All .ttl files in an ontology directory."""
    return sorted(glob.glob(os.path.join(ontology_dir, "*.ttl")))


def _namespace(uri):
    """The namespace part of a URI (up to and including the last # or /)."""
    for sep in ("#", "/"):
        idx = uri.rfind(sep)
        if idx != -1:
            return uri[: idx + 1]
    return uri


# --- mapping side ----------------------------------------------------------

# (yaml-section, list-of-keys-holding a {prefix,name} term)
_TERM_KEYS = ("class", "relation", "value_predicate", "property",
              "property_relation", "predicate")


def _resolve(prefixes, term, where):
    prefix = term.get("prefix")
    name = term.get("name")
    ns = prefixes.get(prefix)
    uri = f"{ns}{name}" if ns else name
    return {"where": where, "prefix": prefix, "name": name, "uri": uri}


def referenced_terms(mapping):
    """Every ontology term referenced by a mapping, with provenance."""
    prefixes = mapping.get("prefixes", {})
    refs = []

    resource = mapping.get("resource", {})
    if "class" in resource:
        refs.append(_resolve(prefixes, resource["class"], "resource.class"))

    for i, prop in enumerate(mapping.get("properties", [])):
        if "predicate" in prop:
            refs.append(_resolve(prefixes, prop["predicate"],
                                 f"properties[{i}].predicate"))

    for i, meas in enumerate(mapping.get("measurements", [])):
        for key in _TERM_KEYS:
            if key in meas and isinstance(meas[key], dict) and "name" in meas[key]:
                refs.append(_resolve(prefixes, meas[key],
                                     f"measurements[{i}].{key}"))
    return refs


def lint_mapping(mapping, known_terms):
    """Return issues for referenced terms missing from a modelled namespace."""
    known_namespaces = {_namespace(t) for t in known_terms}
    issues = []
    for ref in referenced_terms(mapping):
        uri = ref["uri"]
        ns = _namespace(uri)
        if ns in known_namespaces and uri not in known_terms:
            issues.append({
                "where": ref["where"],
                "term": uri,
                "message": f"{ref['prefix']}:{ref['name']} is not defined in the ontology",
            })
    return issues


# --- CLI -------------------------------------------------------------------

def _default_ontology_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "RESONANCE-Ontology"))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tools.mapping_linter",
        description="Check YAML mappings against the RESONANCE ontology.",
    )
    parser.add_argument("mappings", nargs="+", help="YAML mapping file(s)")
    parser.add_argument("--ontology", default=_default_ontology_dir(),
                        help="Path to the RESONANCE-Ontology directory")
    args = parser.parse_args(argv)

    known = load_ontology_terms(ontology_ttls(args.ontology))
    total = 0
    for path in args.mappings:
        with open(path) as f:
            mapping = yaml.safe_load(f)
        issues = lint_mapping(mapping, known)
        total += len(issues)
        if issues:
            print(f"\n{path}: {len(issues)} undefined term(s)")
            for i in issues:
                print(f"  - {i['where']}: {i['message']}")
        else:
            print(f"\n{path}: OK (all terms defined)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
