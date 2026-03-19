# 📡 Semantic Resource Interface Service (SRI-Service)

## 🧾 Overview
The **SRI-Service** is a Streamlit application designed to:

- Subscribe to an MQTT topic and receive incoming data (JSON or raw text)
- Transform incoming data into **RDF (Resource Description Framework)**
- Publish the generated RDF to another MQTT topic
- Provide a real-time UI to monitor incoming and processed data

This tool is intended for **semantic data pipelines, IoT integration, and RDF transformations**.

---

## ⚙️ Features
- MQTT subscriber & publisher
- Real-time data processing with auto-refresh
- JSON to RDF transformation
- Live dashboard with:
  - MQTT connection status
  - Latest message view
  - Message history (last 20 entries)
- Sidebar configuration for MQTT and RDF settings
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

[Open SRI-Service](http:// "Go to SRI_Service")

Notice

A test publisher (test_publisher.py) is included to simulate incoming messages.
The semantic mapper (semantic_mapper.py) will be replaced since it correspondes to the test data.
