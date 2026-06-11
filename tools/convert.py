"""CLI: fetch a live raiprogramming device snapshot and convert it to RDF.

Examples:
    # auto-detect the mapping by snapshot shape
    python -m tools.convert --hems PE7W-G97K-HWKP-P8EE --device 21

    # use a specific mapping, write Turtle to a file
    python -m tools.convert -e PE7W-G97K-HWKP-P8EE -d 35 \\
        --mapping Mappings/raiprogramming_hvac.yaml --out hvac.ttl

    # just show the JSON snapshot the adapter produced
    python -m tools.convert -e PE7W-G97K-HWKP-P8EE -d 129 --snapshot-only

Needs raiprogramming importable (PYTHONPATH=..) and its PCS certificate config.
"""

import argparse
import json
import sys

import yaml

from semantic_mapper import semanticise_data, detect_schema, load_mapping


def pick_mapping(snapshot, mapping_path, mappings_dir):
    """Return (mapping_dict, name) from an explicit path or by auto-detection."""
    if mapping_path:
        return load_mapping(mapping_path), mapping_path
    mapping, name = detect_schema(snapshot, mappings_dir)
    return mapping, name


def _build_parser():
    p = argparse.ArgumentParser(
        prog="tools.convert",
        description="Fetch a raiprogramming device snapshot and convert it to RDF.",
    )
    p.add_argument("--hems", "-e", required=True, help="Household HEMS id")
    p.add_argument("--device", "-d", required=True, help="Device id")
    p.add_argument("--mapping", "-m", default=None,
                   help="YAML mapping file (default: auto-detect)")
    p.add_argument("--mappings-dir", default="Mappings",
                   help="Directory scanned for auto-detect [default: Mappings]")
    p.add_argument("--base-uri", default="http://w3id.org/resonance/resource/")
    p.add_argument("--stat", default="avg", help="avg/min/max [default: avg]")
    p.add_argument("--snapshot-only", action="store_true",
                   help="Print the JSON snapshot and exit (no RDF)")
    p.add_argument("--out", default=None, help="Write RDF to this file")
    return p


def run(argv, fetch=None):
    """Fetch -> (optionally) convert -> output. Returns an exit code."""
    if fetch is None:
        from adapters.raiprogramming.source import fetch_snapshot as fetch

    args = _build_parser().parse_args(argv)
    snapshot = fetch(args.hems, args.device, stat=args.stat)

    if args.snapshot_only:
        print(json.dumps(snapshot, indent=2))
        return 0

    mapping, name = pick_mapping(snapshot, args.mapping, args.mappings_dir)
    if not mapping:
        print(f"No compatible mapping found in {args.mappings_dir!r} for this "
              f"snapshot (device {args.device}).", file=sys.stderr)
        return 1

    rdf = semanticise_data([snapshot], mapping, args.base_uri)
    print(f"# mapping: {name}")          # valid Turtle comment
    if args.out:
        with open(args.out, "w") as f:
            f.write(rdf)
        print(f"# wrote {args.out}")
    else:
        print(rdf)
    return 0


def main():
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
