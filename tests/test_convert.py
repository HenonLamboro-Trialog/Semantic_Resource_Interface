"""Tests for the `tools.convert` CLI (fetch snapshot -> RDF), no live calls."""

import json
import os

from tools import convert

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPINGS_DIR = os.path.join(REPO, "Mappings")

METER_SNAPSHOT = {
    "resource_id": "HEMS1_21",
    "device_type": "EE_METER_ISKRA_AM550",
    "timestamp": "2026-06-10T13:15:00",
    "active_power": {"value": -4834.9, "unit": "W"},
    "voltage_l1": {"value": 231.7, "unit": "V"},
}


def _fetch(hems, device, stat="avg"):
    return METER_SNAPSHOT


def test_explicit_mapping_prints_turtle(capsys):
    code = convert.run(
        ["--hems", "HEMS1", "--device", "21",
         "--mapping", os.path.join(MAPPINGS_DIR, "raiprogramming_meter.yaml")],
        fetch=_fetch,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "sri4all:PowerDevice" in out
    assert "sri4all:hasPowerMeasurement" in out


def test_autodetect_selects_meter_mapping(capsys):
    code = convert.run(
        ["--hems", "HEMS1", "--device", "21", "--mappings-dir", MAPPINGS_DIR],
        fetch=_fetch,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "raiprogramming_meter" in out          # reports which mapping it used
    assert "sri4all:PowerMeasurement" in out


def test_snapshot_only_prints_json(capsys):
    code = convert.run(
        ["--hems", "HEMS1", "--device", "21", "--snapshot-only"],
        fetch=_fetch,
    )
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out)["resource_id"] == "HEMS1_21"


def test_no_matching_mapping_errors(capsys, tmp_path):
    # empty mappings dir -> auto-detect finds nothing
    code = convert.run(
        ["--hems", "HEMS1", "--device", "21", "--mappings-dir", str(tmp_path)],
        fetch=_fetch,
    )
    assert code == 1
    assert "no" in capsys.readouterr().err.lower()
