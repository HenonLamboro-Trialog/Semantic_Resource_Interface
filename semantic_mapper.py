from functools import reduce
import os
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef, XSD
import yaml
import copy

DATATYPE_MAP = {
    "float": XSD.float, "int": XSD.integer, "integer": XSD.integer,
    "string": XSD.string, "datetime": XSD.dateTime, "bool": XSD.boolean
}

def resolve_path(data, path, default=None):
    """Safely traverses a dot-separated path in a nested dictionary."""
    try:
        return reduce(lambda d, k: d[k], path.split("."), data)
    except (KeyError, TypeError):
        return default

def load_mapping(mapping_path):
    with open(mapping_path, "r") as f:
        return yaml.safe_load(f)

def detect_schema(data, mappings_dir="mappings"):
    """Scans mapping files and returns the first one that matches the data structure."""
    if not os.path.exists(mappings_dir):
        return None, None
        
    for file in os.listdir(mappings_dir):
        if file.endswith((".yaml", ".yml")):
            try:
                with open(os.path.join(mappings_dir, file)) as f:
                    cfg = yaml.safe_load(f)
                reqs = cfg.get("match", {}).get("required_fields", [])
                if reqs and all(resolve_path(data, f) is not None for f in reqs):
                    return cfg, file
            except Exception as e:
                print(f"Error parsing {file}: {e}")
    return None, None

def inject_path(item, path, value):
    """Safely handles dot-notation path generation for JSON structures."""
    parts = path.split('.')
    current = item
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value

def resolve_path(item, path):
    """Utility helper to navigate nested object paths."""
    parts = path.split('.')
    current = item
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

def get_uri(namespaces, config_item):
    prefix = config_item.get("prefix")
    name = config_item.get("name")
    if prefix in namespaces:
        return URIRef(f"{namespaces[prefix]}{name}")
    return URIRef(name)

def semanticise_data(data, mapping, base_uri, graph=None):
    data = copy.deepcopy(data)
    if not mapping:
        raise ValueError("Mapping configuration is required.")
    if "resource" not in mapping:
        raise ValueError("Missing resource section.")

    g = graph if isinstance(graph, Graph) else Graph()
    BASE = Namespace(base_uri)
    g.bind("resource", BASE)

    namespaces = {}
    for prefix, uri in mapping.get("prefixes", {}).items():
        namespaces[prefix] = Namespace(uri)
        g.bind(prefix, namespaces[prefix])

    if isinstance(data, dict):
        data_list = [data]
    elif isinstance(data, list):
        data_list = data
    else:
        raise TypeError("Input data must be dict or list of dicts.")

    res_cfg = mapping["resource"]

    for item in data_list:
        for meas in mapping.get("measurements", []):
            if "constant_values" in meas:
                for const in meas["constant_values"]:
                    inject_path(item, const["path"], const["value"])

        res_id = resolve_path(item, res_cfg["id_path"])
        if not res_id:
            raise ValueError(f"Cannot resolve resource id using {res_cfg['id_path']}")
        res_uri = URIRef(f"{base_uri}{res_id}")

        rdf_class = get_uri(namespaces, res_cfg["class"])
        g.add((res_uri, RDF.type, rdf_class))

        for prop in mapping.get("properties", []):
            value = resolve_path(item, prop["path"])
            if value is None:
                continue

            predicate_uri = get_uri(namespaces, prop["predicate"])
            if prop.get("type") == "uri" or prop.get("datatype") == "uri":
                target_prefix = prop.get("prefix")
                object_node = URIRef(f"{namespaces[target_prefix]}{value}") if target_prefix in namespaces else URIRef(value)
            else:
                datatype = DATATYPE_MAP.get(prop.get("datatype", "string"), XSD.string)
                object_node = Literal(value, datatype=datatype)
            g.add((res_uri, predicate_uri, object_node))

        # --- Measurements Core Processing ---
        for meas in mapping.get("measurements", []):
            value = resolve_path(item, meas["path"])
            if value is None:
                continue

            safe_path_suffix = meas["path"].replace('.', '_')
            measurement_uri = URIRef(f"{base_uri}{res_id}_{safe_path_suffix}")

            # Parent Entity Link
            relation_uri = get_uri(namespaces, meas["relation"])
            g.add((res_uri, relation_uri, measurement_uri))

            # Measurement RDF class instantiation
            measurement_class = get_uri(namespaces, meas["class"])
            g.add((measurement_uri, RDF.type, measurement_class))

            datatype = DATATYPE_MAP.get(meas.get("datatype", "float"), XSD.float)
            value_predicate = meas.get("value_predicate", {"prefix": "sri4all", "name": "value"})
            value_uri = get_uri(namespaces, value_predicate)
            g.add((measurement_uri, value_uri, Literal(value, datatype=datatype)))

            # Pattern A: Direct Measurement -> hasUnitOfMeasurment -> Unit Reference
            if "unit_path" in meas:
                unit_val = resolve_path(item, meas["unit_path"])
                if unit_val:
                    unit_pred = get_uri(namespaces, meas.get(
                        "unit_predicate",
                        {"prefix": "sri4all", "name": "hasUnitOfMeasurment"}))
                    u_prefix = meas.get("unit_prefix")
                    if u_prefix and u_prefix in namespaces:
                        g.add((measurement_uri, unit_pred, URIRef(f"{namespaces[u_prefix]}{unit_val}")))

            # Pattern B: Secondary Linked Properties (e.g. ActivePower Property Node)
            if "property" in meas:
                property_uri = URIRef(f"{measurement_uri}_property")
                property_class = get_uri(namespaces, meas["property"])
                
                prop_relation = get_uri(namespaces, meas["property_relation"]) if "property_relation" in meas else get_uri(namespaces, {"prefix": "sri4all", "name": "hasProperty"})
                
                g.add((measurement_uri, prop_relation, property_uri))
                g.add((property_uri, RDF.type, property_class))

                if "property_unit_path" in meas:
                    p_unit_val = resolve_path(item, meas["property_unit_path"])
                    if p_unit_val:
                        unit_pred = get_uri(namespaces, {"prefix": "sri4all", "name": "hasUnitOfMeasurment"})
                        u_prefix = meas.get("unit_prefix")
                        if u_prefix and u_prefix in namespaces:
                            g.add((property_uri, unit_pred, URIRef(f"{namespaces[u_prefix]}{p_unit_val}")))

            # Measurement timeStamp processing
            if "timestamp_path" in meas:
                ts_val = resolve_path(item, meas["timestamp_path"])
                if ts_val:
                    ts_pred = get_uri(namespaces, meas.get(
                        "timestamp_predicate",
                        {"prefix": "sri4all", "name": "timeStamp"}))
                    ts_datatype = DATATYPE_MAP.get(meas.get("timestamp_datatype", "dateTime"), XSD.dateTime)
                    g.add((measurement_uri, ts_pred, Literal(ts_val, datatype=ts_datatype)))

    return g.serialize(format="turtle")

# """
# Author: Henon Mengistu Lamboro
# Email: henon.lamboro@trialog.com
# Created: 2026-03-19
# updated: 2026-06-04
# Description: Processes sensor measurements and generates RDF triples.
# """