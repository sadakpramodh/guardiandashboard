# pages/locations.py

import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
from google.cloud.firestore_v1 import Client
import numpy as np

def show_locations(db: Client):
    st.subheader("🌍 Location Tracker")

    # Select device
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch locations subcollection
    loc_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("locations")
    locs = loc_ref.stream()

    location_data = []
    for loc in locs:
        entry = loc.to_dict()
        if "latitude" in entry and "longitude" in entry:
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            location_data.append(entry)

    if not location_data:
        st.info("No location data found.")
        return

    df = pd.DataFrame(location_data)
    df = df.sort_values("timestamp")

    st.map(df[["latitude", "longitude"]], use_container_width=True)

    # Calculate movement speed (m/s between consecutive points)
    df["time_diff"] = df["timestamp"].diff().dt.total_seconds().fillna(0)
    df["distance"] = np.sqrt((df["latitude"].diff()**2 + df["longitude"].diff()**2)) * 111_000  # approx meters
    df["speed_mps"] = df["distance"] / df["time_diff"]
    df["speed_kmph"] = df["speed_mps"] * 3.6

    st.line_chart(df.set_index("timestamp")["speed_kmph"].fillna(0), use_container_width=True)
    st.caption("📈 Estimated movement speed (km/h) over time")
