import streamlit as st
import queue
import time
import json
import yaml
import os

from mqtt_service import MQTTService
from config import AppConfig
from semantic_mapper import (semanticise_data, detect_schema, load_mapping)
from streamlit_autorefresh import st_autorefresh

# STREAMLIT PAGE CONFIG
st.set_page_config(page_title="Semantic Resource Interface", layout="wide")
st.title("📡 Semantic Resource Interface")

# Global objects
@st.cache_resource
def get_mqtt_queue():
    return queue.Queue()

shared_mqtt_queue = get_mqtt_queue()

def handle_message(payload, mqtt_service_instance):
    shared_mqtt_queue.put(payload)

# Session state initialization 
if "history" not in st.session_state:
    st.session_state.history = []

if "mqtt_service" not in st.session_state:
    st.session_state.mqtt_service = None

if "config" not in st.session_state:
    st.session_state.config = AppConfig()

conf = st.session_state.config

# Sidebar

st.sidebar.header("MQTT Configuration")
conf.broker = st.sidebar.text_input("Broker", conf.broker)

conf.port = st.sidebar.number_input("Port", value=int(conf.port))
conf.subscribe_topic = st.sidebar.text_input("Subscribe Topic", conf.subscribe_topic)
conf.publish_topic = st.sidebar.text_input("Publish Topic (RDF Output)", conf.publish_topic)

# ---------------------------------------------------------

st.sidebar.header("RDF Configuration")
conf.base_uri = st.sidebar.text_input("Base URI", conf.base_uri)
conf.ontology_uri = st.sidebar.text_input("Ontology URI", conf.ontology_uri)

# Mappings
MAPPINGS_DIR = "mappings"

if not os.path.exists(MAPPINGS_DIR):
    os.makedirs(MAPPINGS_DIR)

mapping_files = sorted([
    f for f in os.listdir(MAPPINGS_DIR)
    if f.endswith(".yaml") or f.endswith(".yml")])

# Semantic mapping
st.sidebar.header("Semantic Mapping")
selected_mapping = st.sidebar.selectbox("Select Mapping",["AUTO-DETECT"] + mapping_files)

# SHOW SUPPORTED SCHEMA INFO
if selected_mapping != "AUTO-DETECT":
    try:
        selected_mapping_data = load_mapping(
            os.path.join(MAPPINGS_DIR, selected_mapping))

        st.sidebar.success(
            f"Supported Schema:\n"
            f"{selected_mapping_data.get('schema_name', selected_mapping)}"
        )
    except Exception as e:
        st.sidebar.error(
            f"Mapping load error: {e}")
else:
    st.sidebar.info(
        "AUTO-DETECT enabled.\n"
        "Incoming JSON will be matched automatically.")

# YAML file upload
uploaded_mapping = st.sidebar.file_uploader(
    "Upload Custom Mapping YAML",
    type=["yaml", "yml"]
)
uploaded_mapping_content = None
if uploaded_mapping:
    try:
        uploaded_mapping_content = yaml.safe_load(
            uploaded_mapping)
        st.sidebar.success(
            "Custom mapping loaded successfully.")
    except Exception as e:
        st.sidebar.error(
            f"Invalid YAML file: {e}")

# Mapping preview
with st.sidebar.expander(
    "📄 Mapping Preview",
    expanded=False
):
    if uploaded_mapping_content:
        st.json(uploaded_mapping_content)

    elif selected_mapping != "AUTO-DETECT":
        preview_mapping = load_mapping(
            os.path.join(
                MAPPINGS_DIR,
                selected_mapping
            )
        )
        st.json(preview_mapping)
st.sidebar.divider()

# MQTT controls
if st.sidebar.button(
    "🚀 Start MQTT Service",
    use_container_width=True
):
    if st.session_state.mqtt_service is None:
        try:
            srv = MQTTService(conf,handle_message )
            srv.start()
            st.session_state.mqtt_service = srv
            st.sidebar.success("Connected to MQTT broker.")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.sidebar.error(
                f"Connection error: {e}")
# ---------------------------------------------------------

if st.sidebar.button(
    "🛑 Stop MQTT Service",
    use_container_width=True
):
    if st.session_state.mqtt_service:
        st.session_state.mqtt_service.stop()
        st.session_state.mqtt_service = None
        st.sidebar.warning("MQTT service stopped.")
        st.rerun()

# ---------------------------------------------------------

if st.sidebar.button(
    "🗑️ Clear History",
    use_container_width=True
):
    st.session_state.history = []
    st.rerun()

st_autorefresh(
    interval=200,
    key="mqtt_refresh"
)

# PROCESS MQTT MESSAGES
processed_any = False
while not shared_mqtt_queue.empty():
    try:
        raw_data = shared_mqtt_queue.get_nowait()
        if raw_data.strip().startswith((
            "<",
            "@prefix",
            "PREFIX"
        )):
            continue
        try:
            payload_dict = json.loads(raw_data)

        except json.JSONDecodeError:
            payload_dict = {
                "raw_text": raw_data }

        # VALIDATE PAYLOAD
        if isinstance(payload_dict, dict):
            # Convert single item into list
            payload_list = [payload_dict]
        elif isinstance(payload_dict, list):
            payload_list = payload_dict
        else:
            rdf_out = "Invalid JSON payload."
            mapping_name = "INVALID"
            continue
        try:    
            if uploaded_mapping_content:
                mapping = uploaded_mapping_content
                mapping_name = "Uploaded Mapping"
            elif selected_mapping == "AUTO-DETECT":
                mapping, mapping_name = detect_schema(
                    payload_dict,
                    MAPPINGS_DIR
                )
               
                # NO MATCH FOUND
                if mapping is None:
                    rdf_out = (
                        "No compatible schema mapping found.")
                    mapping_name = "UNMATCHED"
                    st.session_state.history.append({
                        "timestamp": time.strftime("%H:%M:%S"),
                        "payload": payload_dict,
                        "rdf": rdf_out,
                        "mapping": mapping_name
                    })
                    continue
            else:
                mapping = load_mapping(
                    os.path.join(
                        MAPPINGS_DIR,
                        selected_mapping
                    )
                )
                mapping_name = selected_mapping
        
            # RDF GENERATION
            rdf_out = semanticise_data(
                payload_list,
                mapping,
                conf.base_uri,
                conf.ontology_uri
            )
            # MQTT RDF PUBLISH
            if st.session_state.mqtt_service:
                st.session_state.mqtt_service.publish(
                    conf.publish_topic,
                    rdf_out
                )
        except Exception as e:
            rdf_out = f"Mapping Error: {e}"
            mapping_name = "ERROR"
        
        # STORE HISTORY
        st.session_state.history.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "payload": payload_dict,
            "rdf": rdf_out,
            "mapping": mapping_name
        })
        processed_any = True
    except queue.Empty:
        break
# REFRESH UI
if processed_any:
    st.rerun()

# STATUS METRICS
metric_col1, metric_col2 = st.columns(2)
with metric_col1:
    mqtt_status = (
        "🟢 ONLINE"
        if st.session_state.mqtt_service
        else "🔴 OFFLINE"
    )
    st.metric(
        "MQTT Status",
        mqtt_status
    )
with metric_col2:

    st.metric(
        "Messages Received",
        len(st.session_state.history)
    )
st.divider()

# LATEST MESSAGE
if st.session_state.history:
    latest = st.session_state.history[-1]
    st.subheader(
        f"⚡ Latest Payload ({latest['timestamp']})"
    )
    st.caption(
        f"Semantic Mapping Used: {latest['mapping']}"
    )
else:
    st.subheader(
        "⚡ Latest Payload"
    )
# ---------------------------------------------------------

col_json, col_rdf = st.columns(2)
if st.session_state.history:
    with col_json:
        st.write("### Incoming JSON")
        st.json(latest["payload"])
    with col_rdf:
        st.write("### Generated RDF")
        st.code(
            latest["rdf"],
            language="turtle"
        )
        st.download_button(
            "⬇️ Download RDF",
            latest["rdf"],
            file_name="output.ttl",
            mime="text/turtle"
        )
else:
    with col_json:
        st.info(
            "Incoming JSON will appear here..."
        )
    with col_rdf:
        st.info(
            "Generated RDF will appear here..."
        )

# HISTORY
st.divider()
with st.expander(
    "📜 Full Message History (Last 20 Messages)",
    expanded=True
):
    history_to_show = list(
        reversed(st.session_state.history)
    )[:20]
    if history_to_show:
        for i, entry in enumerate(history_to_show):
            msg_id = (
                len(st.session_state.history) - i
            )
            st.markdown(
                f"""
                **Message #{msg_id}**
                — `{entry['timestamp']}`
                """
            )
            st.caption(
                f"Mapping Used: {entry['mapping']}"
            )
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                st.json(
                    entry["payload"]
                )
            with h_col2:
                st.code(
                    entry["rdf"],
                    language="turtle"
                )
            st.divider()
    else:
        st.write("No messages received yet.")