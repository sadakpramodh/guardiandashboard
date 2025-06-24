# pages/phone_state.py

import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud.firestore_v1 import Client

def show_phone_state(db: Client):
    st.subheader("📶 Phone State")

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        # Get devices from the correct path
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="phone_state_device_select")
        if not selected_device:
            return

        # Fetch phone_state subcollection
        state_ref = devices_ref.document(selected_device).collection("phone_state")
        records = state_ref.limit(1000).stream()

        state_data = []
        for rec in records:
            entry = rec.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            state_data.append(entry)

        if not state_data:
            st.info("📶 No phone state data found for this device.")
            return

        df = pd.DataFrame(state_data)
        df = df.sort_values("timestamp", ascending=False)

        # Phone state statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Records", len(df))
        with col2:
            if "networkType" in df.columns:
                current_network = df.iloc[0]["networkType"] if not df.empty else "Unknown"
                st.metric("📡 Current Network", current_network)
        with col3:
            if "callState" in df.columns:
                current_call_state = df.iloc[0]["callState"] if not df.empty else "Unknown"
                st.metric("📞 Call State", current_call_state)
        with col4:
            if "dataState" in df.columns:
                current_data_state = df.iloc[0]["dataState"] if not df.empty else "Unknown"
                st.metric("📊 Data State", current_data_state)

        # Display phone state table
        st.markdown("### 📋 Phone State History")
        display_columns = ["timestamp", "callState", "dataActivity", "dataState", "networkType", "simOperatorName"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            st.dataframe(df[available_columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

        # Phone state analytics
        if not df.empty:
            with st.expander("📊 Phone State Analytics"):
                # Network type distribution
                if "networkType" in df.columns:
                    st.markdown("**📡 Network Type Distribution:**")
                    network_counts = df["networkType"].value_counts()
                    st.bar_chart(network_counts)

                # Call state over time
                if "callState" in df.columns:
                    st.markdown("**📞 Call State Activity:**")
                    call_state_counts = df["callState"].value_counts()
                    st.bar_chart(call_state_counts)

                # Data activity timeline
                if "dataActivity" in df.columns and "timestamp" in df.columns:
                    st.markdown("**📈 Data Activity Timeline:**")
                    df_chart = df.copy()
                    df_chart["date"] = df_chart["timestamp"].dt.date
                    daily_activity = df_chart.groupby("date")["dataActivity"].count()
                    st.line_chart(daily_activity)

    except Exception as e:
        st.error(f"❌ Error loading phone state data: {str(e)}")
        st.info("Check your Firebase connection and data structure.")