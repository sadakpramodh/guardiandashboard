# pages/call_logs.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_call_logs(db: Client):
    st.subheader("📞 Call Logs")

    # Load devices to select from
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch call_logs subcollection
    logs_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("call_logs")
    logs = logs_ref.stream()

    call_data = []
    for log in logs:
        entry = log.to_dict()
        entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
        entry["duration"] = entry.get("duration", 0)
        call_data.append(entry)

    if not call_data:
        st.info("No call logs found for this device.")
        return

    df = pd.DataFrame(call_data)
    df = df.sort_values("timestamp", ascending=False)

    st.dataframe(df, use_container_width=True)

    with st.expander("📊 Call Statistics"):
        st.bar_chart(df["duration"].groupby(df["timestamp"].dt.date).sum())
