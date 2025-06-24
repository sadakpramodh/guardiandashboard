# pages/call_logs.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_call_logs(db: Client):
    st.subheader("📞 Call Logs")

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

        selected_device = st.selectbox("Select a Device ID", device_ids, key="call_logs_device_select")
        if not selected_device:
            return

        # Fetch call_logs subcollection
        logs_ref = devices_ref.document(selected_device).collection("call_logs")
        logs = logs_ref.limit(1000).stream()

        call_data = []
        for log in logs:
            entry = log.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            entry["duration"] = entry.get("duration", 0)
            call_data.append(entry)

        if not call_data:
            st.info("📞 No call logs found for this device.")
            return

        df = pd.DataFrame(call_data)
        df = df.sort_values("timestamp", ascending=False)

        # Call statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📞 Total Calls", len(df))
        with col2:
            st.metric("📤 Outgoing", len(df[df.get('type', '') == 'outgoing']))
        with col3:
            st.metric("📥 Incoming", len(df[df.get('type', '') == 'incoming']))
        with col4:
            total_duration = df["duration"].sum()
            st.metric("⏱️ Total Duration", f"{total_duration//60}m {total_duration%60}s")

        # Display call logs table
        st.markdown("### 📋 Recent Call Logs")
        display_columns = ["timestamp", "phoneNumber", "duration", "type"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            st.dataframe(df[available_columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

        # Call duration chart
        if not df.empty and "duration" in df.columns:
            with st.expander("📊 Call Duration Analysis"):
                df_chart = df.copy()
                df_chart["date"] = df_chart["timestamp"].dt.date
                daily_duration = df_chart.groupby("date")["duration"].sum()
                st.bar_chart(daily_duration)
                st.caption("Daily total call duration (seconds)")

    except Exception as e:
        st.error(f"❌ Error loading call logs: {str(e)}")
        st.info("Check your Firebase connection and data structure.")