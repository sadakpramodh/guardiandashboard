# pages/contacts.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_contacts(db: Client):
    st.subheader("👥 Contacts")

    # Select device
    device_docs = db.collection("devices").stream()
    device_ids = [doc.id for doc in device_docs]

    selected_device = st.selectbox("Select a Device ID", device_ids)
    if not selected_device:
        return

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch contacts subcollection
    contacts_ref = db.collection("users").document(user_email).collection("devices").document(selected_device).collection("contacts")
    contacts = contacts_ref.stream()

    contact_list = []
    for contact in contacts:
        entry = contact.to_dict()
        entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
        contact_list.append(entry)

    if not contact_list:
        st.info("No contacts found for this device.")
        return

    df = pd.DataFrame(contact_list)
    df = df.sort_values("timestamp", ascending=False)

    search = st.text_input("🔍 Search by name or number")
    if search:
        df = df[df.apply(lambda row: search.lower() in str(row.get("contactName", "")).lower()
                                        or search in str(row.get("phoneNumber", "")), axis=1)]

    st.dataframe(df[["contactName", "phoneNumber", "timestamp"]], use_container_width=True)
