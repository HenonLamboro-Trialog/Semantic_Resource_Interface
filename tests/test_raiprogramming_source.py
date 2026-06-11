"""Tests for the raiprogramming source adapter (aggregates -> JSON snapshot).

A fake Household stands in for the live PCS client, so these run without
certificates or the raiprogramming package.
"""

from adapters.raiprogramming.source import (
    device_snapshot, normalize_key, normalize_unit,
)


class FakeHousehold:
    def __init__(self, hems, by_id, aggregates):
        self.hems = hems
        self._by_id = by_id
        self._aggregates = aggregates

    @property
    def devices_by_id(self):
        return self._by_id

    def get_aggregates(self, device, **kwargs):
        return self._aggregates[device]


def _agg(measurements):
    return {"measurements": measurements}


def test_normalize_key_makes_safe_snake_case():
    assert normalize_key("Active power") == "active_power"
    assert normalize_key("Voltage L1") == "voltage_l1"
    assert normalize_key("Import active power - 15 minute average") == \
        "import_active_power_15_minute_average"


def test_normalize_unit_maps_raw_symbols_to_qudt_names():
    assert normalize_unit("°C") == "DEG_C"
    assert normalize_unit("Wh") == "W-HR"
    assert normalize_unit("A") == "Ampere"
    assert normalize_unit("W") == "W"          # already a qudt name
    assert normalize_unit("l/h") == "l/h"      # unknown -> passthrough


def test_snapshot_normalizes_units():
    hh = FakeHousehold(
        hems="HEMS1",
        by_id={35: {"device_id": 35, "device_type": "HEAT_PUMP"}},
        aggregates={35: _agg({
            "Outdoor temp.": {"unit": "°C", "data": [{"bt": "t1", "avg": 8.5}]},
        })},
    )
    snap = device_snapshot(hh, 35)
    assert snap["outdoor_temp"] == {"value": 8.5, "unit": "DEG_C"}


def test_snapshot_has_identity_and_per_sensor_value_unit():
    hh = FakeHousehold(
        hems="HEMS1",
        by_id={21: {"device_id": 21, "device_type": "EE_METER_ISKRA_AM550"}},
        aggregates={21: _agg({
            "Active power": {"unit": "W", "data": [
                {"bt": "2026-06-10T13:00:00", "avg": -4800.0},
                {"bt": "2026-06-10T13:15:00", "avg": -4834.9},
            ]},
            "Voltage L1": {"unit": "V", "data": [
                {"bt": "2026-06-10T13:15:00", "avg": 231.7},
            ]},
        })},
    )

    snap = device_snapshot(hh, 21)

    assert snap["resource_id"] == "HEMS1_21"
    assert snap["device_type"] == "EE_METER_ISKRA_AM550"
    assert snap["timestamp"] == "2026-06-10T13:15:00"
    # latest numeric bucket is used
    assert snap["active_power"] == {"value": -4834.9, "unit": "W"}
    assert snap["voltage_l1"] == {"value": 231.7, "unit": "V"}


def test_snapshot_skips_non_numeric_and_empty_sensors():
    hh = FakeHousehold(
        hems="HEMS1",
        by_id={21: {"device_id": 21, "device_type": "M"}},
        aggregates={21: _agg({
            "State name": {"unit": "", "data": [{"bt": "t1", "avg": "Charging"}]},
            "Empty": {"unit": "W", "data": [{"bt": "t1", "avg": None}]},
            "Active power": {"unit": "W", "data": [{"bt": "t1", "avg": 10.0}]},
        })},
    )

    snap = device_snapshot(hh, 21)

    assert "state_name" not in snap
    assert "empty" not in snap
    assert snap["active_power"]["value"] == 10.0
