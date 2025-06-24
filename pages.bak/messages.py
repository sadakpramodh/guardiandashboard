# pages/messages.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_messages(db: Client):
    st.subheader("💬 Messages")

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

        selected_device = st.selectbox("Select a Device ID", device_ids, key="messages_device_select")
        if not selected_device:
            return

        # Fetch messages subcollection
        messages_ref = devices_ref.document(selected_device).collection("messages")
        messages = messages_ref.limit(1000).stream()

        sms_list = []
        for msg in messages:
            entry = msg.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            sms_list.append(entry)

        if not sms_list:
            st.info("💬 No messages found for this device.")
            return

        df = pd.DataFrame(sms_list)
        df = df.sort_values("timestamp", ascending=False)

        # Message statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💬 Total Messages", len(df))
        with col2:
            if "phoneNumber" in df.columns:
                unique_numbers = df["phoneNumber"].nunique()
                st.metric("📱 Unique Numbers", unique_numbers)
        with col3:
            if "type" in df.columns:
                sent_msgs = len(df[df.get('type', '') == 'sent'])
                st.metric("📤 Sent Messages", sent_msgs)

        # Search functionality
        st.markdown("### 🔍 Search Messages")
        search = st.text_input("Search message content or sender", placeholder="Enter search term...")
        
        if search:
            search_lower = search.lower()
            filtered_df = df[
                df.apply(lambda row: 
                    search_lower in str(row.get("body", "")).lower() or 
                    search_lower in str(row.get("phoneNumber", "")).lower(), axis=1)
            ]
        else:
            filtered_df = df

        # Display messages table
        st.markdown("### 📱 Message History")
        display_columns = ["timestamp", "phoneNumber", "body", "type"]
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if available_columns:
            st.dataframe(filtered_df[available_columns], use_container_width=True)
        else:
            st.dataframe(filtered_df, use_container_width=True)

        # Message analytics
        if not df.empty:
            with st.expander("📊 Message Analytics"):
                # Top senders/receivers
                if "phoneNumber" in df.columns:
                    st.markdown("**📈 Top Contacts by Message Count:**")
                    top_senders = df["phoneNumber"].value_counts().head(10)
                    st.bar_chart(top_senders)

                # Messages per day
                if "timestamp" in df.columns:
                    st.markdown("**📅 Daily Message Activity:**")
                    df_chart = df.copy()
                    df_chart["date"] = df_chart["timestamp"].dt.date
                    daily_counts = df_chart.groupby("date").size()
                    st.line_chart(daily_counts)

    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")
        st.info("Check your Firebase connection and data structure.")