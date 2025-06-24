# pages/contacts.py

import streamlit as st
import pandas as pd
from google.cloud.firestore_v1 import Client
from datetime import datetime

def show_contacts(db: Client):
    st.subheader("👥 Contacts")

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

        selected_device = st.selectbox("Select a Device ID", device_ids, key="contacts_device_select")
        if not selected_device:
            return

        # Fetch contacts subcollection
        contacts_ref = devices_ref.document(selected_device).collection("contacts")
        contacts = contacts_ref.limit(1000).stream()

        contact_list = []
        for contact in contacts:
            entry = contact.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            contact_list.append(entry)

        if not contact_list:
            st.info("👥 No contacts found for this device.")
            return

        df = pd.DataFrame(contact_list)
        df = df.sort_values("timestamp", ascending=False)

        # Contact statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("👥 Total Contacts", len(df))
        with col2:
            if "contactName" in df.columns:
                unique_names = df["contactName"].nunique()
                st.metric("📝 Unique Names", unique_names)

        # Search functionality
        st.markdown("### 🔍 Search Contacts")
        search = st.text_input("Search by name or phone number", placeholder="Enter name or number...")
        
        if search:
            search_lower = search.lower()
            filtered_df = df[
                df.apply(lambda row: 
                    search_lower in str(row.get("contactName", "")).lower() or 
                    search in str(row.get("phoneNumber", "")), axis=1)
            ]
        else:
            filtered_df = df

        # Display contacts table
        st.markdown("### 📋 Contact List")
        display_columns = ["contactName", "phoneNumber", "timestamp"]
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        
        if available_columns:
            st.dataframe(filtered_df[available_columns], use_container_width=True)
        else:
            st.dataframe(filtered_df, use_container_width=True)

        # Contact statistics
        if not df.empty:
            with st.expander("📊 Contact Analysis"):
                if "contactName" in df.columns:
                    # Most recent contacts
                    recent_contacts = df.head(10)
                    st.markdown("**📅 Most Recent Contacts:**")
                    for _, contact in recent_contacts.iterrows():
                        st.write(f"• {contact.get('contactName', 'Unknown')} - {contact.get('phoneNumber', 'N/A')}")

    except Exception as e:
        st.error(f"❌ Error loading contacts: {str(e)}")
        st.info("Check your Firebase connection and data structure.")