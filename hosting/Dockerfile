FROM python:3.14.4-alpine

WORKDIR /sri-service

# Copied from requirements.txt
RUN pip install streamlit streamlit-autorefresh paho-mqtt rdflib

COPY /sri-service/. .

CMD [ "streamlit","run","app.py", "--browser.gatherUsageStats", "false", "--server.headless", "true", "--server.address", "0.0.0.0", "--server.port", "8501" ]
