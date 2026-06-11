# Fleet conversion coverage — status

Live audit of the RESONANCE PCS fleet via `tools/fleet_audit.py` (device
**configuration** only — device types + sensors with units; no measurement
fetches). Raw run in `fleet-coverage-report.txt`.

**Fleet:** 42 households · 145 devices · 39 device types.

## Headline

| Metric | First audit | + mappings | + sensor-alias layer |
|---|---|---|---|
| Device types with a mapping | 23 / 39 | 27 / 39 | **30 / 39** |
| Device types with **no** mapping | 16 | 12 | **9** (of which **3 have no telemetry** → 6 real gaps) |
| Devices with a mapping | ~118 | ~129 | **~132 / 145 (91%)** |

Biggest wins: **SOLAR_SOLAREDGE** (19 devices / 19 households) via
`raiprogramming_pv_string`; pure batteries (`BATTERY_CET`, `BATTERY_HOY`) and the
NIBE heat pump now covered via the sensor-alias layer (no new mappings).

## Extensions made (this round)

**Ontology** (`RESONANCE-Ontology`, branch `feature/sync-sri4all-with-diagram`)
- `sri4all:Frequency` — electric frequency measurement (aligned to QUDT / SAREF).
- New module **`SRI4Storage`** — `Battery` + `StateOfCharge` / `StateOfHealth` /
  `Capacity` (+ `has*` relations), reusing SRI4ALL for power/energy/V/I/temp.
- `ONTOLOGY-DEVELOPMENT-LOG.md` — append-only decision/research log.

**Mappings** (`Semantic_Resource_Interface`, 8 total, all lint clean)
- `raiprogramming_battery` (uses `SRI4Storage`) — live-verified on the Deye hybrid.
- `raiprogramming_pv_string` — string inverters (SolarEdge/Huawei/Deye-string/
  Austa) — live-verified on a reporting SolarEdge.
- (existing: meter, hvac, pv-hybrid, charger, sensor)

**Source adapter**
- **Sensor-alias layer** (`canonical_key`) — collapses *unambiguous* vendor sensor
  names onto canonical keys (`state_of_charge → battery_state_of_charge`,
  `outdoor_temperature → outdoor_temp`, …) so one mapping covers a device family
  across vendors. Ambiguous names (e.g. `active_power`, which differs on a meter
  vs a battery) are deliberately **not** aliased.
- Unit normalization + `frequency → sri4all:Frequency` on the meter mapping.

**Tooling**
- `tools/fleet_audit.py` — this coverage audit.

## Remaining gaps (9 uncovered types)

The sensor-alias layer resolved the battery (`BATTERY_CET`, `BATTERY_HOY`) and
NIBE heat-pump variants. What's left:

### A. No numeric telemetry — nothing to convert (3)
`HEAT_PUMP_KRONOTERM_TT3000`, `HYBRID_VILION_ENERARK`, `EE_METER_SANGXING_S34U18`
— expose no sensors with units. Not a mapping gap; flagged for data/integration.

### B. Match-discriminator edge cases (3)
Aliasing can't help these — they lack the field a mapping matches on, and a
single AND-only `match` can't cover both shapes without colliding with another
mapping.
| Type | Issue |
|---|---|
| `SOLAR_DEYE_STRING_3P`, `SOLAR_AUSTA_STRING_3P` | AC-only string inverters: `active_power` + `ac_current_*` but **no `pv_voltage`**. A DC-less pv_string variant would cover them (kept off the main pv_string match to avoid regressing the DC-only `SOLAR_DEYE_HYBRID`). |
| `EMULATION_ELECTRICITY_METER` | `active_power` + `current_*` but **no voltage** — meter match requires `voltage_l1` (the meter/charger discriminator). |

### C. New small mappings / match tweaks (3)
| Type | Need |
|---|---|
| `SHELLY_TEMPERATURE_GEN_2` | temperature-only sensor mapping (current sensor mapping requires temp **and** humidity) |
| `CHARGER_V2CHARGE_TRYDAN` | broaden charger match (only exposes `per_phase_current_setpoint`) |
| `HVAC_PEGO_ECP200_BASE` | refrigeration controller — map `ambient_temperature` / `evaporator_temperature` to TemperatureMeasurement |

## Cross-cutting issues (affect matched types too)

1. **Incomplete coverage on matched meters** — the largest pool of unmapped
   sensors. Per meter: `import/export_active_power` (directional), `frequency`,
   reactive power/energy, **tariff energies** (`*_tariff_1/2`), and the
   `*_minute_average` variants.
   - `frequency` → **done** (mapped to `sri4all:Frequency` on the meter mapping).
   - directional import/export → needs the diagram's `FlowDirection`
     (production/consumption); blocked on a mapper feature to attach a fixed
     individual via an object property.
   - reactive **energy** and **tariff** energy → no ontology class yet.
   - `*_minute_average` → intentionally skipped (redundant with the base sensor).

2. **Auto-detect collisions on multi-role devices** — a hybrid/inverter matches
   more than one mapping:
   - `SOLAR_HUAWEI_SUN2000` → `meter` **and** `pv_string` (has grid V/I *and* PV V).
   - `HYBRID_DEYE_HYBRID_3P_HV` → `battery` **and** `pv`.
   `detect_schema` returns the first match (order-dependent). Needs mapping
   **priority/specificity**, or explicit `--mapping` for multi-role devices.

3. **Mapper feature gaps** (tracked for the SRI service):
   - attach a fixed individual via an object property (for `FlowDirection`,
     `isAboutCommodityQuantity`).
   - per-snapshot multi-type resources (a hybrid is PV **and** battery).

## Suggested next steps (priority order)
1. **Sensor-alias layer** in `adapters/raiprogramming/source.py` — collapse vendor
   sensor-name variants to canonical keys. Fixes most of bucket **B** at once and
   reduces future per-vendor mappings.
2. Add `frequency` (and, once modelled, reactive/tariff energy) to the meter
   mapping.
3. Mapping priority for auto-detect; explicit handling of hybrids.
4. Small mappings for bucket **C**.
5. Ontology: reactive-energy + tariff-energy classes; `FlowDirection` usage.
