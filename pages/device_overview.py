# pages/device_overview.py

import streamlit as st
from google.cloud.firestore_v1 import Client

def show_device_overview(db: Client):
    st.subheader("📱 Device Overview")

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    # Fetch device metadata collection
    devices = db.collection("users").document(user_email).collection("devices").stream()
    device_map = {doc.id: doc.to_dict() for doc in devices}

    if not device_map:
        st.warning("No devices found in Firestore.")
        return

    device_ids = list(device_map.keys())
    selected_device = st.selectbox("Select a Device", device_ids)

    if selected_device:
        device = device_map[selected_device]

        st.markdown("### Device Metadata")
        cols = st.columns(3)
        with cols[0]:
            st.write(f"**Model:** {device.get('model', '-')}") 
            st.write(f"**Brand:** {device.get('brand', '-')}") 
            st.write(f"**Android Version:** {device.get('androidVersion', '-')}") 
        with cols[1]:
            st.write(f"**Device ID:** {device.get('deviceId', '-')}") 
            st.write(f"**Manufacturer:** {device.get('manufacturer', '-')}") 
            st.write(f"**Hardware:** {device.get('hardware', '-')}") 
        with cols[2]:
            st.write(f"**Network Operator:** {device.get('networkOperatorName', '-')}") 
            st.write(f"**SIM Operator:** {device.get('simOperatorName', '-')}") 
            st.write(f"**Phone Type:** {device.get('phoneType', '-')}") 

        st.markdown("---")
        st.write("Full Metadata JSON:")
        st.json(device)
