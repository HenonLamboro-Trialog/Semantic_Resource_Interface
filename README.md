# 📡 Semantic Resource Interface Service (SRI-Service)

## 🧾 Overview
The **SRI-Service** is a Streamlit application designed to:

- Subscribe to an MQTT topic and receive incoming data (JSON or raw text)
- Transform incoming data into **RDF (Resource Description Framework)** based on YAML mapping file
- Publish the generated RDF to MQTT topic
- Provide a real-time UI to monitor incoming and processed data

This tool is intended for **semantic data pipelines, IoT integration, and RDF transformations**.

---

## ⚙️ Features
- MQTT subscriber & publisher
- Real-time data processing with auto-refresh
- JSON to RDF transformation with YAML mapping file
- Live dashboard with:
  - MQTT connection status
  - Latest message view
  - Message history (last 20 entries)
- Sidebar configuration for MQTT and Ontology settings
- Session-based history management

---


---

## Installation

### 1. Clone the repository
```bash
git clone <http://gitlab.lan.trialog.com/resonance/sri-service.git>
cd <repo-name>
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Running the Application
```bash
streamlit run app.py
```
## Access the UI: 

[Open SRI-Service](https://sri-resonance.trialog.com/)


# YAML Mapping Guide

This guide explains how to create a YAML mapping file for converting new JSON/MQTT data into RDF using the semantic mapper.

---
Before creating a new schema, you must understand both:

1. The structure of the incoming data.
2. The ontology concepts that represent that data.(Link to the Ontology)

# 1. Understand the JSON Data

Example:

```json
{
  "resource_id": "sensor_001",
  "value": 23.5,
  "unit": "Celsius"
}
```

For each field, decide whether it is:

* **Resource Identifier** → identifies the device/resource
* **Measurement** → sensor reading or measured value

---

# 2. Define Ontology Prefixes

Add every ontology used by the mapping.

```yaml
prefixes:
  sri4all: "https://w3id.org/resonance/SRI4ALL#"
  s4ener: "https://saref.etsi.org/saref4ener/"
```

---

# 3. Define the Resource

Specify:

* The unique identifier field (`id_path`)
* The ontology class representing the device

```yaml
resource:
  id_path: resource_id

  class:
    prefix: sri4all
    name: TemperatureSensor
```

Generated RDF:

```ttl
resource:sensor_001 rdf:type sri4all:TemperatureSensor .
```

---

# 4. Map Measurements

Use `measurements` for values produced by sensors or devices.

JSON:

```json
{
  "value": 23.5
}
```

YAML:

```yaml
measurements:

  - path: value

    class:
      prefix: sri4all
      name: TemperatureMeasurement

    relation:
      prefix: sri4all
      name: hasTemperatureMeasurement

    datatype: float
```

Generated RDF:

```ttl
resource:sensor_001
    sri4all:hasTemperatureMeasurement resource:sensor_001_value .
```

---

# 5. Choose the Correct Ontology

| Data Type                              | Ontology           |
| -------------------------------------- | ------------------ |
| Devices, Measurements, Building Assets | SRI4ALL            |
| PV Systems               | SRI4PV             |
| Voltage, Current, Energy Concepts      | SAREF / SAREF4ENER |

Always reuse existing ontology classes and properties whenever possible.

---

# Complete Example

JSON:

```json
{
  "resource_id": "sensor_002",
  "type": "TemperatureSensor",
  "value": 23.5,
  "unit": "Celsius",
  "timestamp": "2026-02-24T10:30:00"
}
```

YAML:

```yaml
schema_name: temperature_sensor

prefixes:
  sri4all: "https://w3id.org/resonance/SRI4ALL#"
  saref: "https://saref.etsi.org/core/"
  xsd: "http://www.w3.org/2001/XMLSchema#"
  unit: "http://qudt.org/vocab/unit/"

resource:
  id_path: resource_id
  class:
    prefix: saref
    name: Sensor

measurements:
  - path: value
    class:
      prefix: sri4all
      name: TemperatureMeasurement
    relation:
      prefix: sri4all
      name: hasTemperatureMeasurement
    datatype: float

    naming_pattern: "Measurement_{res_id}"

    unit_path: unit
    unit_prefix: unit
    
    timestamp_path: timestamp
    timestamp_datatype: dateTime

```

---

Notice

A test publisher (test_publisher.py) is included to simulate incoming messages.


