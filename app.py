import streamlit as st
import queue
import time
import json
from mqtt_service import MQTTService
from config import AppConfig
from semantic_mapper import semanticise_data 
from streamlit_autorefresh import st_autorefresh


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


# Streamlit App UI

st.set_page_config(page_title="Semantic Resource Interface", layout="wide")
st.title("📡 Semantic Resource Interface")

# Sidebar Configuration
st.sidebar.header("MQTT Configuration")
conf = st.session_state.config
conf.broker = st.sidebar.text_input("Broker", conf.broker)
conf.port = st.sidebar.number_input("Port", value=int(conf.port))
conf.subscribe_topic = st.sidebar.text_input("Subscribe Topic", conf.subscribe_topic)
conf.publish_topic = st.sidebar.text_input("Publish Topic (RDF data)", conf.publish_topic)
st.sidebar.header("RDF Configuration")
conf.base_uri = st.sidebar.text_input("Base URI", conf.base_uri)
conf.ontology_uri = st.sidebar.text_input("Ontology URI", conf.ontology_uri)


st.sidebar.divider()

# Controls

if st.sidebar.button("🚀 Start MQTT Service", use_container_width=True):
    if st.session_state.mqtt_service is None:
        try:
            srv = MQTTService(conf, handle_message)
            srv.start()
            st.session_state.mqtt_service = srv
            st.sidebar.success("Connected!")
            time.sleep(0.5)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

if st.sidebar.button("🛑Stop MQTT Service", use_container_width=True):
    if st.session_state.mqtt_service:
        st.session_state.mqtt_service.stop()
        st.session_state.mqtt_service = None
        st.sidebar.warning("Disconnected.")
        st.rerun()

if st.sidebar.button("🗑️ Clear History", use_container_width=True):
    st.session_state.history = []
    st.rerun()


while not shared_mqtt_queue.empty():
    try:
        raw_data = shared_mqtt_queue.get_nowait()
        
        try:
            payload_dict = json.loads(raw_data)
        except json.JSONDecodeError:
            if raw_data.strip().startswith(("<", "@prefix", "PREFIX")):
                continue
            payload_dict = {"raw_text": raw_data}

        # semantisation  
        try:
            rdf_out = semanticise_data(payload_dict, conf.base_uri, conf.ontology_uri)
            
            # Auto-publish back to MQTT
            if st.session_state.mqtt_service:
                st.session_state.mqtt_service.publish(conf.publish_topic, rdf_out)
        except Exception as e:
            rdf_out = f"Mapping Error: {e}"

        # 3. History Entry
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "payload": payload_dict,
            "rdf": rdf_out
        }
        st.session_state.history.append(entry)
            
    except queue.Empty:
        break


# 4. Data processing

st_autorefresh(interval=200, key="mqtt_fast_refresh")

processed_any = False
while not shared_mqtt_queue.empty():
    try:
        raw_data = shared_mqtt_queue.get_nowait()
        
        if raw_data.strip().startswith(("<", "@prefix", "PREFIX")):
            continue

        try:
            payload_dict = json.loads(raw_data)
        except json.JSONDecodeError:
            payload_dict = {"raw_text": raw_data}

        # Semantic Mapping
        try:
            rdf_out = semanticise_data(payload_dict, conf.base_uri, conf.ontology_uri)
            
            if st.session_state.mqtt_service:
                st.session_state.mqtt_service.publish(conf.publish_topic, rdf_out)
        except Exception as e:
            rdf_out = f"Mapping Error: {e}"

        st.session_state.history.append({
            "timestamp": time.strftime("%H:%M:%S"),
            "payload": payload_dict,
            "rdf": rdf_out
        })
        processed_any = True
            
    except queue.Empty:
        break

if processed_any:
    st.rerun()

# Display Side-by-Side

# Status 
status_col1, status_col2, status_col3 = st.columns(3)
with status_col1:
    status_text = "🟢 ONLINE" if st.session_state.mqtt_service else "🔴 OFFLINE"
    st.metric("MQTT Status", status_text)
with status_col2:
    st.metric("Messages Received", len(st.session_state.history))
# with status_col3:
#     st.metric("Queue Size", shared_mqtt_queue.qsize())

st.divider()

# B. Latest Transaction Section 
if st.session_state.history:
    latest = st.session_state.history[-1]
    st.subheader(f"⚡ Latest Payload ({latest['timestamp']})")
else:
    st.subheader("⚡ Latest Payload")

# Always create the columns
col_top_json, col_top_rdf = st.columns(2)

# Fill the columns based on whether data exists
if st.session_state.history:
    with col_top_json:
        st.write("**Incoming JSON**")
        st.json(latest['payload'])
    with col_top_rdf:
        st.write("**Outgoing RDF**")
        st.code(latest['rdf'], language="turtle")
else:
    with col_top_json:
        st.info("Incoming JSON will appear here...")
    with col_top_rdf:
        st.info("Generated RDF will appear here...")

# Full History Section 
st.divider()


# Updated History Section 
with st.expander("📜 Full Message History (Last 20 Messages)", expanded=True):
    history_to_show = list(reversed(st.session_state.history))[:20]
    
    if history_to_show:
        for i, entry in enumerate(history_to_show):
            msg_id = len(st.session_state.history) - i
            st.markdown(f"**Message #{msg_id}** — `{entry['timestamp']}`")
            
            h_c1, h_c2 = st.columns(2)
            with h_c1:
                st.json(entry['payload'])
            with h_c2:
                st.code(entry['rdf'], language="turtle")
            st.divider()
    else:
        st.write("No messages yet.")