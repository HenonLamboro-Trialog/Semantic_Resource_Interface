# Example conversions — household PE7W-G97K-HWKP-P8EE (Velenje pilot)

Real RDF produced from live PCS data by the raiprogramming source adapter +
`tools/convert.py`, using the diagram-aligned mappings. Regenerate any of these:

```bash
PYTHONPATH=.. python -m tools.convert --hems PE7W-G97K-HWKP-P8EE --device <id> [--out file.ttl]
```

| File | Device | Mapping | Contents |
|------|--------|---------|----------|
| `P8EE_dev21_meter.ttl` | 21 — Iskra AM550 meter | `raiprogramming_meter` | PowerDevice + active power (ActivePower) + 3× Voltage + 3× Current |
| `P8EE_dev21_meter_snapshot.json` | 21 | — | the JSON snapshot the adapter built (pre-RDF) |
| `P8EE_dev35_hvac.ttl` | 35 — Kronoterm heat pump | `raiprogramming_hvac` | HeatPump + 5× TemperatureMeasurement (outdoor/supply/return/sanitary/room) + power |
| `P8EE_dev129_pv.ttl` | 129 — Deye hybrid inverter | `raiprogramming_pv` | Photovoltaic + 4× PowerMeasurement (PV/inverter/grid/battery) + Voltage + Current |
| `P8EE_dev124_meter_chint.ttl` | 124 — Chint DTSU666 meter | `raiprogramming_meter` | PowerDevice + active & reactive power + 3× Voltage + 3× Current |
| `P8EE_dev82_charger.ttl` | 82 — OCPP EV charger | `raiprogramming_charger` | PowerDevice + active power + current + session energy |
| `P8EE_dev116_sensor.ttl` | 116 — Shelly H&T | `raiprogramming_sensor` | saref:Sensor + TemperatureMeasurement + sri4weather:Humidity |

| `P8EE_dev129_battery.ttl` | 129 — Deye hybrid (battery side) | `raiprogramming_battery` | sri4storage:Battery + StateOfCharge + Capacity + power/voltage/current |
| `SolarEdge_7458_dev144_pv_string.ttl` | 144 — SolarEdge string inverter (hems 7458-…) | `raiprogramming_pv_string` | Photovoltaic + 3×AC + PV Voltage/Current + active power |

EV chargers are modelled as `sri4all:PowerDevice` for now — the ontology has no
EVSE/Connector/ChargingStation classes yet (SRI4EV would be a separate task).
Device 342 (Vilion battery) exposes no numeric telemetry, so it has no example.

Vocabulary follows the SRI4ALL diagram (`RESONANCE-Ontology/Diagrams/sri4all.png`):
`sri4all:value`, `sri4all:timeStamp`, `sri4all:hasUnitOfMeasurment`, and the
`hasPowerMeasurement` / `hasTemperatureMeasurement` / `hasMeasurement` relations.
Values are point-in-time and will differ on each run.
