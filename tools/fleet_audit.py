"""Audit a raiprogramming fleet: can every device be converted, and what's missing?

Works from device *configuration* only (device types + sensor names/units) -- no
measurement fetches -- so it is fast and side-effect free. For each device it
reports which mapping (if any) auto-detects it, which numeric sensors that
mapping covers, and which numeric sensors no mapping covers yet.

CLI:
    PYTHONPATH=.. python -m tools.fleet_audit            # whole fleet
    PYTHONPATH=.. python -m tools.fleet_audit --hems <id> # one household
"""

import argparse
import glob
import os
import sys
from collections import defaultdict

import yaml

from adapters.raiprogramming.source import canonical_key


# --- pure coverage logic ---------------------------------------------------

def _key(path):
    return path.split(".")[0]


def mapping_match_keys(mapping):
    """Snapshot keys a mapping requires to auto-detect (minus resource_id)."""
    reqs = mapping.get("match", {}).get("required_fields", [])
    return {_key(f) for f in reqs if f != "resource_id"}


def mapping_path_keys(mapping):
    """Snapshot keys a mapping converts."""
    return {_key(m["path"]) for m in mapping.get("measurements", []) if "path" in m}


def analyze_device(numeric_keys, mappings):
    """Match a device's numeric sensor keys against the mappings.

    Returns {matched: [names], covered: set, unmapped: set}.
    A mapping matches if all its match keys are present; covered keys are the
    union of matched mappings' path keys that the device actually has.
    """
    numeric_keys = set(numeric_keys)
    matched = [name for name, m in mappings.items()
               if mapping_match_keys(m) and mapping_match_keys(m) <= numeric_keys]
    covered = set()
    for name in matched:
        covered |= mapping_path_keys(mappings[name]) & numeric_keys
    return {"matched": matched, "covered": covered,
            "unmapped": numeric_keys - covered}


def load_mappings(mappings_dir):
    out = {}
    for path in sorted(glob.glob(os.path.join(mappings_dir, "*.yaml"))):
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        out[os.path.basename(path)] = cfg
    return out


# --- live fleet walk -------------------------------------------------------

def numeric_keys_for_device(household, device_id):
    """Normalized keys of a device's numeric sensors (those with a unit)."""
    units = household.devices_sensors_unit.get(device_id, {})
    return {canonical_key(s): u for s, u in units.items()}


def audit_household(household, mappings):
    """Per-device audit for one household. Returns a list of device reports."""
    reports = []
    by_id = household.devices_by_id
    for device_id, dev in by_id.items():
        keyed_units = numeric_keys_for_device(household, device_id)
        result = analyze_device(set(keyed_units), mappings)
        reports.append({
            "device_id": device_id,
            "device_type": dev.get("device_type"),
            "category": dev.get("device_category"),
            "n_numeric": len(keyed_units),
            **result,
            "units": keyed_units,
        })
    return reports


def audit_fleet(fleet, household_factory, mappings, only_hems=None):
    """Walk the fleet; yield (hems, [device reports])."""
    hemses = [only_hems] if only_hems else list(fleet.households.values())
    for i, hems in enumerate(hemses, 1):
        print(f"  [{i}/{len(hemses)}] {hems}", file=sys.stderr)
        try:
            hh = household_factory(hems)
            yield hems, audit_household(hh, mappings)
        except Exception as e:                       # noqa: BLE001
            yield hems, [{"error": str(e)}]


# --- reporting / CLI -------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(prog="tools.fleet_audit")
    parser.add_argument("--hems", default=None, help="Audit a single household")
    parser.add_argument("--mappings-dir", default="Mappings")
    parser.add_argument("--show-devices", action="store_true",
                        help="Print a per-device line for every household")
    args = parser.parse_args(argv)

    from raiprogramming import FleetManagement, Household
    mappings = load_mappings(args.mappings_dir)
    fleet = FleetManagement()

    by_type = defaultdict(lambda: {"devices": 0, "households": set(),
                                   "matched": set(), "no_match": 0,
                                   "unmapped": defaultdict(int)})
    unmatched_devices = 0
    total_devices = 0

    for hems, reports in audit_fleet(fleet, lambda h: Household(hems=h), mappings,
                                     only_hems=args.hems):
        for r in reports:
            if "error" in r:
                print(f"  ! {hems}: {r['error']}", file=sys.stderr)
                continue
            total_devices += 1
            t = by_type[r["device_type"]]
            t["devices"] += 1
            t["households"].add(hems)
            if r["matched"]:
                t["matched"].update(r["matched"])
            else:
                t["no_match"] += 1
                if r["n_numeric"]:
                    unmatched_devices += 1
            for k in r["unmapped"]:
                t["unmapped"][k] += 1
            if args.show_devices:
                tag = ",".join(r["matched"]) or "NO MATCH"
                print(f"{hems} dev {r['device_id']} {r['device_type']} "
                      f"[{tag}] {len(r['covered'])}/{r['n_numeric']} sensors covered")

    print("\n==================== FLEET COVERAGE BY DEVICE TYPE ====================")
    for t, info in sorted(by_type.items(), key=lambda kv: -kv[1]["devices"]):
        mapped = ",".join(sorted(info["matched"])) or "— NO MAPPING —"
        print(f"\n{t}  ({info['devices']} devices, {len(info['households'])} households)")
        print(f"    mapping: {mapped}"
              + (f"   [{info['no_match']} unmatched]" if info["no_match"] else ""))
        if info["unmapped"]:
            top = sorted(info["unmapped"].items(), key=lambda kv: -kv[1])
            print("    unmapped numeric sensors: "
                  + ", ".join(f"{k}({n})" for k, n in top))

    print(f"\nTotal devices: {total_devices}; device types: {len(by_type)}; "
          f"device types with no mapping: "
          f"{sum(1 for i in by_type.values() if not i['matched'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
