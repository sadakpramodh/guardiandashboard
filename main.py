# main.py – Single file Streamlit dashboard (prevents auto navigation)

import streamlit as st
from auth import login
from firebase_admin import credentials, firestore, initialize_app
import os
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Guardian Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit's default navigation
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {visibility: hidden;}
div[data-testid="stDecoration"] {visibility: hidden;}
div[data-testid="stStatusWidget"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize Firebase Admin SDK (only once)
@st.cache_resource
def init_firebase():
    """Initialize Firebase Admin SDK with caching to avoid reinitialization"""
    try:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not cred_path:
            st.error("⚠️ GOOGLE_APPLICATION_CREDENTIALS not set in .env file")
            st.stop()
            
        if not os.path.exists(cred_path):
            st.error(f"⚠️ Firebase credentials file not found at: {cred_path}")
            st.info("Make sure the file path in .env matches your actual JSON file location")
            st.stop()

        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(cred_path)
        initialize_app(cred)
        
        return firestore.client()
        
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {str(e)}")
        st.info("Check your Firebase credentials and ensure the service account has proper permissions")
        st.stop()

# Page Functions
def show_device_overview(db):
    st.subheader("📱 Device Overview")

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        # Fetch device metadata collection
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_map = {doc.id: doc.to_dict() for doc in devices}

        if not device_map:
            st.warning("⚠️ No devices found in Firestore.")
            st.info("Make sure your Android app is sending data to Firebase.")
            return

        device_ids = list(device_map.keys())
        selected_device = st.selectbox("Select a Device", device_ids, key="device_overview_select")

        if selected_device:
            device = device_map[selected_device]

            st.markdown("### 📊 Device Information")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📱 Device Model", device.get('device', 'Unknown'))
                st.metric("🏭 Brand", device.get('brand', 'Unknown'))
                st.metric("🤖 Android Version", device.get('androidVersion', 'Unknown'))
                
            with col2:
                st.metric("🔧 Hardware", device.get('hardware', 'Unknown'))
                st.metric("🏗️ Build ID", device.get('buildId', 'Unknown')[:10] + "..." if device.get('buildId') else 'Unknown')
                st.metric("📡 Network Operator", device.get('networkOperatorName', 'Unknown'))
                
            with col3:
                st.metric("📞 Device ID", device.get('deviceId', 'Unknown')[:10] + "..." if device.get('deviceId') else 'Unknown')
                st.metric("📶 IMEI Status", device.get('imei', 'Unknown'))
                st.metric("🔋 Active Status", "✅ Active" if device.get('isActive', False) else "❌ Inactive")

            with st.expander("🔍 Detailed Device Information"):
                st.json(device)

    except Exception as e:
        st.error(f"❌ Error loading devices: {str(e)}")

def show_locations(db):
    st.subheader("🌍 Location Tracker")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="location_device_select")
        if not selected_device:
            return

        loc_ref = devices_ref.document(selected_device).collection("locations")
        locs = loc_ref.limit(1000).stream()

        location_data = []
        for loc in locs:
            entry = loc.to_dict()
            if "latitude" in entry and "longitude" in entry:
                entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
                location_data.append(entry)

        if not location_data:
            st.info("📍 No location data found for this device.")
            return

        df = pd.DataFrame(location_data)
        df = df.sort_values("timestamp")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Total Locations", len(df))
        with col2:
            st.metric("📅 First Record", df["timestamp"].min().strftime("%Y-%m-%d"))
        with col3:
            st.metric("⏰ Last Record", df["timestamp"].max().strftime("%Y-%m-%d"))
        with col4:
            st.metric("🗓️ Days Tracked", (df["timestamp"].max() - df["timestamp"].min()).days)

        map_data = df[["latitude", "longitude"]].copy()
        map_data.columns = ["lat", "lon"]
        st.map(map_data, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading location data: {str(e)}")

def show_call_logs(db):
    st.subheader("📞 Call Logs")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="call_logs_device_select")
        if not selected_device:
            return

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

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading call logs: {str(e)}")

def show_contacts(db):
    st.subheader("👥 Contacts")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="contacts_device_select")
        if not selected_device:
            return

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

        search = st.text_input("🔍 Search by name or number")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.get("contactName", "")).lower()
                                            or search in str(row.get("phoneNumber", "")), axis=1)]

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading contacts: {str(e)}")

def show_messages(db):
    st.subheader("💬 Messages")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="messages_device_select")
        if not selected_device:
            return

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

        search = st.text_input("🔍 Search message body or sender")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.get("body", "")).lower()
                                            or search.lower() in str(row.get("phoneNumber", "")).lower(), axis=1)]

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")

def show_phone_state(db):
    st.subheader("📶 Phone State")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="phone_state_device_select")
        if not selected_device:
            return

        state_ref = devices_ref.document(selected_device).collection("phone_state")
        records = state_ref.limit(1000).stream()

        state_data = []
        for rec in records:
            entry = rec.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            state_data.append(entry)

        if not state_data:
            st.info("📶 No phone state data found.")
            return

        df = pd.DataFrame(state_data)
        df = df.sort_values("timestamp", ascending=False)

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading phone state data: {str(e)}")

def show_weather(db):
    st.subheader("🌦️ Weather Logs")

    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="weather_device_select")
        if not selected_device:
            return

        weather_ref = devices_ref.document(selected_device).collection("weather")
        records = weather_ref.limit(1000).stream()

        weather_data = []
        for rec in records:
            entry = rec.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            weather_data.append(entry)

        if not weather_data:
            st.info("🌦️ No weather data found.")
            return

        df = pd.DataFrame(weather_data)
        df = df.sort_values("timestamp", ascending=False)

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading weather data: {str(e)}")

def main():
    """Main application logic"""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # App header
    st.markdown('<div class="main-header"><h1>🛡️ Guardian Dashboard</h1><p>Real-time Device Monitoring & Analytics</p></div>', unsafe_allow_html=True)

    # Authentication check
    if not login():
        st.info("👆 Please log in to access the dashboard")
        return

    # Initialize Firebase
    db = init_firebase()

    # Sidebar navigation
    st.sidebar.title("📊 Navigation")
    st.sidebar.markdown("---")
    
    # Page selection
    pages = {
        "📱 Device Overview": show_device_overview,
        "📞 Call Logs": show_call_logs,
        "👥 Contacts": show_contacts,
        "💬 Messages": show_messages,
        "🌍 Location Tracker": show_locations,
        "📶 Phone State": show_phone_state,
        "🌦️ Weather Data": show_weather
    }
    
    selected_page = st.sidebar.selectbox(
        "Choose a section:",
        list(pages.keys()),
        index=0
    )
    
    # User info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(f"🔐 Logged in as:\n{st.session_state.email}")
    
    if st.sidebar.button("🚪 Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Display selected page
    try:
        pages[selected_page](db)
    except Exception as e:
        st.error(f"❌ Error loading {selected_page}: {str(e)}")
        st.info("This might be due to missing data or network issues. Please try refreshing the page.")

if __name__ == "__main__":
    main()