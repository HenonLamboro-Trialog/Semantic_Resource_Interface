"""raiprogramming source adapter: PCS aggregates -> JSON snapshot.

Produces a single latest-value snapshot per device, shaped for the YAML
semantic mapper:

    {
      "resource_id": "<hems>_<device_id>",
      "device_type": "EE_METER_ISKRA_AM550",
      "timestamp": "2026-06-10T13:15:00",
      "active_power": {"value": -4834.9, "unit": "W"},
      "voltage_l1":   {"value": 231.7,   "unit": "V"},
      ...
    }

Only numeric sensors are included (text sensors like 'State name' and empty
buckets are dropped). Sensor names are normalized to safe snake_case keys that
a YAML mapping references by `path`.
"""

import logging
import re

log = logging.getLogger(__name__)


def normalize_key(sensor_name):
    """Turn a raiprogramming sensor name into a safe snake_case JSON key."""
    key = sensor_name.strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    return key.strip("_")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def device_snapshot(household, device_id, stat="avg"):
    """Build a latest-value snapshot dict for one device."""
    aggregates = household.get_aggregates(device_id)
    device = household.devices_by_id.get(device_id, {})

    snapshot = {
        "resource_id": f"{household.hems}_{device_id}",
        "device_type": device.get("device_type"),
    }

    latest_ts = None
    for sensor_name, mdata in aggregates.get("measurements", {}).items():
        numeric = [p for p in mdata.get("data", []) if _is_number(p.get(stat))]
        if not numeric:
            continue
        last = numeric[-1]
        snapshot[normalize_key(sensor_name)] = {
            "value": last[stat],
            "unit": mdata.get("unit"),
        }
        bt = last.get("bt")
        if bt and (latest_ts is None or bt > latest_ts):
            latest_ts = bt

    snapshot["timestamp"] = latest_ts
    return snapshot


def fetch_snapshot(hems, device_id, stat="avg"):
    """Construct a live Household and return its device snapshot.

    raiprogramming is imported lazily so the offline tests do not require it.
    """
    from raiprogramming import Household

    return device_snapshot(Household(hems=hems), device_id, stat=stat)
