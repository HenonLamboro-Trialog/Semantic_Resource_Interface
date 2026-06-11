"""Tests for the pure coverage logic of the fleet audit."""

from tools.fleet_audit import mapping_match_keys, mapping_path_keys, analyze_device

METER = {
    "match": {"required_fields": ["resource_id", "active_power.value", "voltage_l1.value"]},
    "measurements": [
        {"path": "active_power.value"},
        {"path": "voltage_l1.value"},
        {"path": "reactive_power.value"},
    ],
}
SENSOR = {
    "match": {"required_fields": ["resource_id", "temperature.value", "relative_humidity.value"]},
    "measurements": [{"path": "temperature.value"}, {"path": "relative_humidity.value"}],
}
MAPPINGS = {"raiprogramming_meter": METER, "raiprogramming_sensor": SENSOR}


def test_match_keys_strip_value_and_resource_id():
    assert mapping_match_keys(METER) == {"active_power", "voltage_l1"}


def test_path_keys_are_snapshot_keys():
    assert mapping_path_keys(METER) == {"active_power", "voltage_l1", "reactive_power"}


def test_device_fully_matched_reports_matched_and_coverage():
    keys = {"active_power", "voltage_l1", "voltage_l2", "reactive_power", "frequency"}
    r = analyze_device(keys, MAPPINGS)
    assert r["matched"] == ["raiprogramming_meter"]
    assert r["covered"] == {"active_power", "voltage_l1", "reactive_power"}
    # voltage_l2 and frequency are real sensors no mapping covers
    assert r["unmapped"] == {"voltage_l2", "frequency"}


def test_device_with_no_matching_mapping():
    keys = {"battery_state_of_charge", "off_grid"}
    r = analyze_device(keys, MAPPINGS)
    assert r["matched"] == []
    assert r["covered"] == set()
    assert r["unmapped"] == {"battery_state_of_charge", "off_grid"}
