# SRI service ↔ RESONANCE-Ontology conformance gap report

**Date:** 2026-06-11
**Context:** Adding a raiprogramming (PCS) source adapter to the SRI service. While
authoring an ontology-conformant mapping we found that the existing mappings and
the mapper's hard-coded defaults reference terms that are **not defined** in the
`RESONANCE-Ontology` reference TTLs. This report lists the gaps so the ontology
owner can decide, per item, whether to **add the term to the ontology** or
**change the mapping/mapper to use an existing term**.

All findings below are reproducible:

```bash
python -m tools.mapping_linter Mappings/*.yaml --ontology ../RESONANCE-Ontology
```

---

## 1. Undefined terms in the existing mappings (from the linter)

**`Mappings/power_sensor.yaml` — 11 undefined terms**

| Where | Term used | Status / suggested existing term |
|---|---|---|
| measurements[0].relation | `sri4all:hasPowerMeasurement` | undefined → use `sri4all:measuresPower` (PowerDevice→PowerMeasurement) or `sri4all:consistsOfPowerMeasurement` (Resource→PowerMeasurement) |
| measurements[1].class | `sri4all:EnergyMeasurement` | undefined → no energy class in `sri4all` (see §3) |
| measurements[1].relation | `sri4all:hasEnergyMeasurement` | undefined |
| measurements[2].class | `sri4all:Current` | undefined (see §3) |
| measurements[2].relation | `sri4all:hasPowerMeasurement` | undefined |
| measurements[3].class | `sri4all:Voltage` | undefined (see §3) |
| measurements[3].relation | `sri4all:hasPowerMeasurement` | undefined |
| measurements[4–5].class | `sri4all:TemperatureMeasurement` | defined in **`sri4building`**, not `sri4all` (wrong prefix) |
| measurements[4–5].relation | `sri4all:hasTemperatureMeasurement` | undefined |

**`Mappings/temprature_sensor.yaml` — 2 undefined terms**

| Where | Term used | Status |
|---|---|---|
| measurements[0].class | `sri4all:TemperatureMeasurement` | lives in `sri4building`, not `sri4all` |
| measurements[0].relation | `sri4all:hasTemperatureMeasurement` | undefined |

## 2. Mapper hard-coded predicates that are not in the ontology

`semantic_mapper.py` emits these by default; none exist in `RESONANCE-Ontology`:

| Default predicate emitted | Ontology actually defines | Notes |
|---|---|---|
| `sri4all:value` (default `value_predicate`) | `sri4all:powerValue` (PowerMeasurement) / `sri4building:hasValue` | per-measurement-type value property |
| `sri4all:hasUnitOfMeasurment` (unit) | `sri4all:isMeasuredIn` (→ qudt:Unit) | also a **spelling error** ("Measurment") |
| `sri4all:timeStamp` (timestamp) | `sri4all:timestamp` (lowercase s) | case mismatch |
| `sri4all:hasProperty` (default `property_relation`) | `sri4all:hasPowerProperty` | |

**Fix applied on this branch:** `unit_predicate` and `timestamp_predicate` are now
overridable per measurement (defaults unchanged, backward compatible), so a mapping
can emit the conformant `isMeasuredIn` / `timestamp`. See
`Mappings/raiprogramming_meter.yaml` for a fully conformant example (lints clean).
The remaining defaults (`value`, `hasUnitOfMeasurment`, `hasProperty`) should be
corrected at the source — either in the ontology or as new mapper defaults.

## 3. Ontology coverage gaps (terms the data needs but the ontology lacks)

Real meter / heat-pump data needs concepts the ontology does not define, which is
why those sensors currently can't be mapped conformantly:

- **Voltage**, **Current**, **Frequency** measurement classes (+ their value/unit
  properties) — common electricity-meter quantities.
- **Energy** measurement in `sri4all` — there is `sri4building:EnergyConsumption` /
  `ElectricityConsumption`, but nothing energy-related in `sri4all`.
- **Temperature** in `sri4all` — `TemperatureMeasurement` exists only in
  `sri4building`; decide whether sensors should reference it there or promote it.
- A way to attach a fixed **`s4ener:CommodityQuantity`** individual (e.g.
  `ElectricPowerL1`) to a measurement — the mapper has no feature to link an
  object property to an existing named individual (only literals, or new property
  nodes). `sri4all:isAboutCommodityQuantity` therefore can't be expressed yet.

## 4. Other issues found

- **`app.py`** calls `semanticise_data(payload, mapping, conf.base_uri, conf.ontology_uri)`,
  but the 4th positional parameter is `graph`, not `ontology_uri` — so
  `ontology_uri` is silently ignored.
- **AUTO-DETECT can't match the existing mappings:** `detect_schema()` requires a
  `match.required_fields` list, which `power_sensor.yaml` and
  `temprature_sensor.yaml` don't have. (`raiprogramming_meter.yaml` adds one.)
- **`semantic_mapper.py`** defines `resolve_path` twice (the second shadows the
  first).
- **`requirements.txt`** does not list `pyyaml` although `semantic_mapper`/`app`
  import `yaml` (works only transitively today).
- Minor: `"KilloV"` unit typo in `power_sensor.yaml`.

## 5. Recommendation

The vocabulary used by the service and the vocabulary defined by the ontology have
diverged. Suggested resolution order:
1. Decide §3 coverage (add Voltage/Current/Energy/etc., or scope them out).
2. Align §1/§2 to existing ontology terms (or add them), then re-run the linter as a
   gate in CI so mappings can't drift from the ontology again.
3. Apply §4 fixes.

The `tools/mapping_linter.py` added on this branch is intended to be that CI gate.
