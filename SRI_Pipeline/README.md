# RESONANCE WP3_T3.1 - Semantic Resource Interface (SRI)

A Python-based semantic resource interface has been implemented for the RESONANCE project data exchange that converts various resource data into RDF format using ontologies via MQTT. 

### Purpose of SRI_Pipeline:
1. **Input**: Accepting input data from various sources (manual JSON, JSON/CSV files).
2. **Processing**: Converting data into RDF triples to standardize and semantize the information.
3. **Publishing**: Sharing semantized RDF data to MQTT topics for integration with other RESONANCE components.

### Script Functionality Overview:
1. **`ConfigLoader`**:
   - Loads environment variables from a `.env` file.
   - Retrieves MQTT broker configuration (broker, port, client ID) for use in the system.

2. **`Main Script`**:
   - Manages user interaction for processing data types (`ev`, `pv`, `building`, etc.).
   - Loads MQTT configuration via `ConfigLoader`.
   - Allows manual or file-based JSON/CSV data input.
   - Processes data by passing it to a semantic interface for RDF conversion and MQTT publishing.

3. **`MQTTClient`**:
   - Handles MQTT operations, including connecting to a broker, subscribing to topics, and publishing messages.
   - Supports JSON encoding for MQTT payloads.
   - Provides hooks (`on_connect`, `on_message`) for handling broker interactions.

4. **`RDFConverter`**:
   - Converts input data (e.g., PV measurements, building data) into RDF triples.
   - Uses RDF namespaces (e.g., `SAREF`, `SRI4BUILDING`) to add ontologies.
   - Binds RDF namespaces to a graph and processes data into a Turtle RDF format.
   - Customizes processing logic for specific data types, e.g., PV production or building data.

5. **`SemanticInterface`**:
   - Bridges MQTT communication and RDF data processing.
   - Converts input data into RDF using the `RDFConverter`.
   - Publishes semantic data to MQTT topics based on the data type (e.g., `pv`, `building`).
   - Handles specific topic routing for hardcoded partners or generic topics.


## Prerequisites

- Python 3.8 or higher
- MQTT Broker (e.g., Mosquitto, HiveMQ)
- Basic understanding of RDF concepts and MQTT

## Setup

1. Clone the repository:
   ```bash
   git clone https://gitlab.trialog.com/resonance/sri.git
   cd SRI_Pipeline
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure MQTT broker settings in `SRI-Implementation/settings.env`
   ```
   MQTT_BROKER=broker_address
   MQTT_PORT=port
   MQTT_CLIENT_ID=semantic_interface
   ```
## Usage

1. Start the interface:
   ```bash
   python main.py
   ```
2. Interactive Data Input:
   The interface will present an interactive prompt:

   a. Select Resource Type:
   ```
   Semantic Resource Interface
   Available resource and service types: ev, pv, hvac, building, weather
   Enter resource type (or 'quit' to exit): 
   ```

   b. Choose Input Format:
   ```
   Enter '1' to input a JSON data or '2' to upload a JSON file or '3' to upload CSV file:
   ```

   c. Provide Data:
   - Example 
      - For JSON input:
     ```
     Enter JSON data: {"temperature": 22.5, "humidity": 45, "mode": "cooling"}
     ```
      - For JSON file:
     ```
     Enter JSON file path: sri/SRI_Pipeline/data_input/PVProductionData_input.json
     ```
     - For CSV file:
     ```
     Enter CSV file path: sri/SRI_Pipeline/data_input/BuildingData_input.csv 
     ```

2. Publishing Data:
   - Publish JSON data to appropriate MQTT topics:
     ```
     Data processed and published successfully!
     ```

3. Example RDF Payload:

   PV RDF Data:
   ```
   @prefix saref4ener: <https://saref.etsi.org/saref4ener/> .
   @prefix sri4all: <https://w3id.org/resonance/sri4all#> .
   @prefix sri4pv: <https://w3id.org/resonance/sri4pv#> .
   @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

   <https:/w3id.org/resonance/pv/measurement/1> a sri4all:PowerMeasurement ;
      saref4ener:CommodityQuantity "ElectricPowerL1" ;
      sri4all:isMeasuredIn "Watt" ;
      sri4all:powerValue "1500"^^xsd:float ;
      sri4pv:isAbout sri4pv:Photovoltaic ;
      sri4pv:timestamp "2024-08-17T14:30:00+00:00"^^xsd:dateTime .
   ```


4. Accessing Semantic Data:
   - Subscribe to corresponding semantic topics:
   ```
    resonance/sri/partner1/site1/pv     # Example PV data topic
   ```

## SRI Usage Notice

Current Status: The RDF converter Currently supports PV production and building data located under the path SRI_Pipeline/data_input. To enable support for additional data types, mappings to the relevant ontologies need to be configured.