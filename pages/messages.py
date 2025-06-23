# pages/messages.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_messages(db: Client):
    st.subheader("💬 Messages")

    # Select device
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch messages subcollection
    messages_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("messages")
    messages = messages_ref.stream()

    sms_list = []
    for msg in messages:
        entry = msg.to_dict()
        entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
        sms_list.append(entry)

    if not sms_list:
        st.info("No messages found for this device.")
        return

    df = pd.DataFrame(sms_list)
    df = df.sort_values("timestamp", ascending=False)

    search = st.text_input("🔍 Search message body or sender")
    if search:
        df = df[df.apply(lambda row: search.lower() in str(row.get("body", "")).lower()
                                        or search.lower() in str(row.get("phoneNumber", "")).lower(), axis=1)]

    st.dataframe(df[["phoneNumber", "body", "timestamp"]], use_container_width=True)

    with st.expander("📊 Top Senders"):
        top_senders = df["phoneNumber"].value_counts().head(10)
        st.bar_chart(top_senders)
