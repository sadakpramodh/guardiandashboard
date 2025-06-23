# pages/weather.py

import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud.firestore_v1 import Client


def show_weather(db: Client):
    st.subheader("🌦 Weather Logs")

    # Select device
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch weather subcollection
    weather_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("weather")
    records = weather_ref.stream()

    weather_data = []
    for rec in records:
        entry = rec.to_dict()
        entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
        weather_data.append(entry)

    if not weather_data:
        st.info("No weather data found.")
        return

    df = pd.DataFrame(weather_data)
    df = df.sort_values("timestamp", ascending=False)

    st.dataframe(df[["city_name", "description", "temperature", "humidity", "wind_speed", "timestamp"]], use_container_width=True)

    with st.expander("📈 Temperature & Humidity Over Time"):
        st.line_chart(df.set_index("timestamp")[["temperature", "humidity"]])
