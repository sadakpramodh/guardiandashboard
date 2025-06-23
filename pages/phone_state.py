# pages/phone_state.py

import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud.firestore_v1 import Client

def show_phone_state(db: Client):
    st.subheader("📶 Phone State")

    # Select device
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch phone_state subcollection
    state_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("phone_state")
    records = state_ref.stream()

    state_data = []
    for rec in records:
        entry = rec.to_dict()
        entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
        state_data.append(entry)

    if not state_data:
        st.info("No phone state data found.")
        return

    df = pd.DataFrame(state_data)
    df = df.sort_values("timestamp", ascending=False)

    st.dataframe(df[["callState", "dataActivity", "dataState", "networkType", "simOperatorName", "timestamp"]], use_container_width=True)

    with st.expander("📊 Network Type Distribution"):
        st.bar_chart(df["networkType"].value_counts())
