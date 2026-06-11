# Adapters & mapping tools

Additions that connect external data sources to the SRI service and keep YAML
mappings honest against the RESONANCE ontology.

## `adapters/raiprogramming/` — PCS source adapter

Turns live raiprogramming (Prosumer Cloud Service) device data into the JSON the
YAML semantic mapper consumes. `device_snapshot(household, device_id)` produces a
latest-value snapshot:

```json
{
  "resource_id": "PE7W-G97K-HWKP-P8EE_21",
  "device_type": "EE_METER_ISKRA_AM550",
  "timestamp": "2026-06-10T13:15:00",
  "active_power":   {"value": -4834.9, "unit": "W"},
  "reactive_power": {"value": 12.0,    "unit": "VAr"}
}
```

Only numeric sensors are kept; names are normalized to snake_case keys that a
mapping references by `path`. `fetch_snapshot(hems, device_id)` is the live entry
point (lazily imports `raiprogramming`, needs its certs/config); `device_snapshot`
is pure and testable with a fake household.

This snapshot is then converted to RDF by `semantic_mapper.semanticise_data` using
a mapping such as `Mappings/raiprogramming_meter.yaml` (ontology-conformant).

## `tools/mapping_linter.py` — ontology-conformance linter

Checks that every term a YAML mapping references is actually defined in the
`RESONANCE-Ontology` TTLs. Terms in namespaces the ontology doesn't model (xsd,
qudt units) are skipped, so only genuine "undefined term" problems are reported.

```bash
# from the repo root; --ontology defaults to ../../RESONANCE-Ontology
python -m tools.mapping_linter Mappings/raiprogramming_meter.yaml \
    --ontology ../RESONANCE-Ontology
```

Exit code is non-zero if any undefined terms are found — suitable as a CI gate.
See `docs/ontology-conformance-gap-report.md` for the current findings.

## Tests

```bash
pip install -r requirements.txt          # adds pyyaml; rdflib already present
python -m pytest tests/ -q
```

The raiprogramming source adapter is tested with a fake household, so no
certificates are required.
