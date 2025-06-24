# main.py – Complete Enhanced Guardian Dashboard with Firebase Role Management

import streamlit as st
from auth import login
from firebase_admin import credentials, firestore, initialize_app
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import json
import requests
from firebase_role_manager import FirebaseRoleManager
from admin_management import show_admin_dashboard

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

# Initialize Firebase Admin SDK using environment variables
@st.cache_resource
def init_firebase():
    """Initialize Firebase Admin SDK with environment variables"""
    try:
        # Create credentials dictionary from environment variables
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Validate required fields
        required_fields = ["project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if not firebase_config.get(field)]
        
        if missing_fields:
            st.error(f"⚠️ Missing Firebase configuration: {', '.join(missing_fields)}")
            st.info("Please check your .env file for missing Firebase credentials")
            st.stop()

        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
        
        return firestore.client()
        
    except Exception as e:
        st.error(f"❌ Firebase initialization failed: {str(e)}")
        st.info("Check your Firebase credentials in .env file")
        st.stop()

# Helper Functions
def format_duration(seconds):
    """Convert seconds to minutes and seconds format"""
    if pd.isna(seconds) or seconds == 0:
        return "0m 0s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"

def get_call_type_name(call_type):
    """Convert call type number to readable name"""
    call_types = {
        1: "📞 Incoming",
        2: "📤 Outgoing", 
        3: "📵 Missed",
        4: "📧 Voicemail",
        5: "🚫 Rejected",
        6: "⛔ Blocked"
    }
    return call_types.get(call_type, f"❓ Unknown ({call_type})")

def get_message_type_name(msg_type):
    """Convert message type number to readable name"""
    message_types = {
        1: "📥 Received",
        2: "📤 Sent",
        3: "📝 Draft", 
        4: "📤 Outbox",
        5: "❌ Failed",
        6: "⏳ Queued"
    }
    return message_types.get(msg_type, f"❓ Unknown ({msg_type})")

def get_user_location_info():
    """Get user's location information"""
    try:
        # Try to get IP geolocation
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": data.get("ip", "Unknown"),
                "city": data.get("city", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "location": f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
            }
    except:
        pass
    
    return {
        "ip": "Unknown",
        "city": "Unknown", 
        "country": "Unknown",
        "location": "Unknown"
    }

def show_user_device_selector(role_manager, current_user_email):
    """Show user and device selector based on Firebase permissions"""
    
    # Get accessible users for current user
    accessible_users = role_manager.get_accessible_users(current_user_email)
    
    if not accessible_users:
        st.sidebar.warning("No accessible users found")
        return None, None
    
    st.sidebar.markdown("### 👥 User & Device Selection")
    
    # User selection
    user_emails = [user["email"] for user in accessible_users]
    
    if len(user_emails) == 1:
        selected_user = user_emails[0]
        st.sidebar.info(f"👤 Viewing: {selected_user}")
    else:
        selected_user = st.sidebar.selectbox(
            "👤 Select User",
            user_emails,
            key="user_selector"
        )
    
    if selected_user:
        # Get devices for selected user
        user_email_sanitized = role_manager.sanitize_email(selected_user)
        
        try:
            devices_ref = role_manager.db.collection("users").document(user_email_sanitized).collection("devices")
            devices = devices_ref.stream()
            device_map = {doc.id: doc.to_dict() for doc in devices}
            
            if not device_map:
                st.sidebar.warning(f"No devices found for {selected_user}")
                return selected_user, None
            
            device_ids = list(device_map.keys())
            selected_device = st.sidebar.selectbox(
                "📱 Select Device",
                device_ids,
                key="device_selector"
            )
            
            return selected_user, selected_device
            
        except Exception as e:
            st.sidebar.error(f"Error fetching devices: {str(e)}")
            return selected_user, None
    
    return None, None

# Page Functions with Firebase Role-Based Access Control
def show_device_overview(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "device_overview"):
        st.error("🚫 Access Denied: You don't have permission to view device overview")
        return
    
    st.subheader(f"📱 Device Overview - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        device_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device)
        device_doc = device_ref.get()
        
        if not device_doc.exists:
            st.warning("⚠️ Device not found.")
            return
        
        device = device_doc.to_dict()

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
        st.error(f"❌ Error loading device overview: {str(e)}")

def show_locations(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "locations"):
        st.error("🚫 Access Denied: You don't have permission to view locations")
        return
    
    # Check if user can see this specific user's location data
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's location data")
        return
    
    st.subheader(f"🌍 Location Tracker - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)

        # Date and time filters
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            hour_range = st.select_slider(
                "🕐 Select Hour Range", 
                options=list(range(24)), 
                value=(0, 23),
                format_func=lambda x: f"{x:02d}:00"
            )

        loc_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("locations")
        
        # Filter by date and hour
        start_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour_range[0]))
        end_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour_range[1], minute=59, second=59))
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        locs = loc_ref.where("timestamp", ">=", start_timestamp).where("timestamp", "<=", end_timestamp).limit(1000).stream()

        location_data = []
        for loc in locs:
            entry = loc.to_dict()
            if "latitude" in entry and "longitude" in entry:
                entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
                location_data.append(entry)

        if not location_data:
            st.info(f"📍 No location data found for {selected_date} between {hour_range[0]:02d}:00 and {hour_range[1]:02d}:00")
            return

        df = pd.DataFrame(location_data)
        df = df.sort_values("timestamp")

        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Total Locations", len(df))
        with col2:
            st.metric("⏰ First Record", df["timestamp"].min().strftime("%H:%M:%S"))
        with col3:
            st.metric("⏰ Last Record", df["timestamp"].max().strftime("%H:%M:%S"))
        with col4:
            duration = df["timestamp"].max() - df["timestamp"].min()
            st.metric("⌛ Duration", f"{duration.total_seconds()/3600:.1f}h")

        # Create path visualization using Plotly
        st.markdown("### 🗺️ Location Path")
        
        if len(df) > 1:
            fig = go.Figure()
            
            # Add path as lines
            fig.add_trace(go.Scattermapbox(
                mode="markers+lines",
                lon=df['longitude'],
                lat=df['latitude'],
                marker={'size': 8, 'color': 'red'},
                line={'width': 3, 'color': 'blue'},
                text=df['timestamp'].dt.strftime('%H:%M:%S'),
                name="Location Path"
            ))
            
            # Add start point
            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=[df.iloc[0]['longitude']],
                lat=[df.iloc[0]['latitude']],
                marker={'size': 15, 'color': 'green'},
                text="Start",
                name="Start Point"
            ))
            
            # Add end point
            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=[df.iloc[-1]['longitude']],
                lat=[df.iloc[-1]['latitude']],
                marker={'size': 15, 'color': 'red'},
                text="End",
                name="End Point"
            ))
            
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(
                    center=dict(
                        lat=df['latitude'].mean(),
                        lon=df['longitude'].mean()
                    ),
                    zoom=13
                ),
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Single point map
            map_data = df[["latitude", "longitude"]].copy()
            map_data.columns = ["lat", "lon"]
            st.map(map_data, use_container_width=True)

        # Recent locations table
        with st.expander("📋 Location Records"):
            display_df = df[["timestamp", "latitude", "longitude"]].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading location data: {str(e)}")

def show_call_logs(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "call_logs"):
        st.error("🚫 Access Denied: You don't have permission to view call logs")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's call logs")
        return
    
    st.subheader(f"📞 Call Logs - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        logs_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("call_logs")
        logs = logs_ref.limit(1000).stream()

        call_data = []
        for log in logs:
            entry = log.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            entry["duration"] = entry.get("duration", 0)
            entry["type_name"] = get_call_type_name(entry.get("type", 0))
            entry["duration_formatted"] = format_duration(entry.get("duration", 0))
            call_data.append(entry)

        if not call_data:
            st.info("📞 No call logs found for this device.")
            return

        df = pd.DataFrame(call_data)
        df = df.sort_values("timestamp", ascending=False)

        # Enhanced statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📞 Total Calls", len(df))
        with col2:
            incoming_count = len(df[df['type'] == 1])
            st.metric("📞 Incoming", incoming_count)
        with col3:
            outgoing_count = len(df[df['type'] == 2])
            st.metric("📤 Outgoing", outgoing_count)
        with col4:
            missed_count = len(df[df['type'] == 3])
            st.metric("📵 Missed", missed_count)

        # Display enhanced call logs table
        st.markdown("### 📋 Call History")
        
        display_df = df[["timestamp", "phoneNumber", "type_name", "duration_formatted"]].copy()
        display_df.columns = ["Time", "Phone Number", "Type", "Duration"]
        display_df["Time"] = display_df["Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        st.dataframe(display_df, use_container_width=True)

        # Call analytics
        with st.expander("📊 Call Analytics"):
            col1, col2 = st.columns(2)
            
            with col1:
                type_counts = df['type_name'].value_counts()
                fig_pie = px.pie(values=type_counts.values, names=type_counts.index, 
                               title="Call Type Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                df_daily = df.copy()
                df_daily['date'] = df_daily['timestamp'].dt.date
                daily_counts = df_daily.groupby('date').size().reset_index(name='count')
                
                fig_line = px.line(daily_counts, x='date', y='count', 
                                 title="Daily Call Activity")
                st.plotly_chart(fig_line, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading call logs: {str(e)}")

def show_contacts(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "contacts"):
        st.error("🚫 Access Denied: You don't have permission to view contacts")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's contacts")
        return
    
    st.subheader(f"👥 Contacts - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        contacts_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("contacts")
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
        search = st.text_input("🔍 Search by name or number")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.get("contactName", "")).lower()
                                            or search in str(row.get("phoneNumber", "")), axis=1)]

        # Display contacts table
        display_columns = ["contactName", "phoneNumber", "timestamp"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading contacts: {str(e)}")

def show_messages(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "messages"):
        st.error("🚫 Access Denied: You don't have permission to view messages")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's messages")
        return
    
    st.subheader(f"💬 Messages - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        messages_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("messages")
        messages = messages_ref.limit(1000).stream()

        sms_list = []
        for msg in messages:
            entry = msg.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            entry["type_name"] = get_message_type_name(entry.get("type", 0))
            sms_list.append(entry)

        if not sms_list:
            st.info("💬 No messages found for this device.")
            return

        df = pd.DataFrame(sms_list)
        df = df.sort_values("timestamp", ascending=False)

        # Enhanced message statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💬 Total Messages", len(df))
        with col2:
            received_count = len(df[df['type'] == 1])
            st.metric("📥 Received", received_count)
        with col3:
            sent_count = len(df[df['type'] == 2])
            st.metric("📤 Sent", sent_count)
        with col4:
            if "phoneNumber" in df.columns:
                unique_contacts = df["phoneNumber"].nunique()
                st.metric("👥 Unique Contacts", unique_contacts)

        # Search functionality
        search = st.text_input("🔍 Search message content or sender")
        if search:
            df = df[df.apply(lambda row: search.lower() in str(row.get("body", "")).lower()
                                            or search.lower() in str(row.get("phoneNumber", "")).lower(), axis=1)]

        # Display enhanced messages table
        st.markdown("### 📱 Message History")
        
        display_columns = ["timestamp", "phoneNumber", "type_name", "body"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            display_df.columns = ["Time", "Phone Number", "Type", "Message"]
            display_df["Time"] = display_df["Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
            # Truncate long messages
            if "Message" in display_df.columns:
                display_df["Message"] = display_df["Message"].astype(str).apply(
                    lambda x: x[:50] + "..." if len(x) > 50 else x
                )
            st.dataframe(display_df, use_container_width=True)

        # Message analytics
        with st.expander("📊 Message Analytics"):
            col1, col2 = st.columns(2)
            
            with col1:
                type_counts = df['type_name'].value_counts()
                fig_pie = px.pie(values=type_counts.values, names=type_counts.index,
                               title="Message Type Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                df_daily = df.copy()
                df_daily['date'] = df_daily['timestamp'].dt.date
                daily_counts = df_daily.groupby('date').size().reset_index(name='count')
                
                fig_line = px.line(daily_counts, x='date', y='count',
                                 title="Daily Message Activity")
                st.plotly_chart(fig_line, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading messages: {str(e)}")

def show_phone_state(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "phone_state"):
        st.error("🚫 Access Denied: You don't have permission to view phone state")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's phone state")
        return
    
    st.subheader(f"📶 Phone State - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        state_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("phone_state")
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
        display_columns = ["timestamp", "callState", "dataActivity", "dataState", "networkType", "simOperatorName"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

        # Phone state analytics
        with st.expander("📊 Phone State Analytics"):
            if "networkType" in df.columns:
                network_counts = df["networkType"].value_counts()
                fig_bar = px.bar(x=network_counts.index, y=network_counts.values,
                               title="Network Type Distribution")
                st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading phone state data: {str(e)}")

def show_weather(role_manager, selected_user, selected_device):
    if not role_manager.can_access_feature(st.session_state.email, "weather"):
        st.error("🚫 Access Denied: You don't have permission to view weather data")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's weather data")
        return
    
    st.subheader(f"🌦️ Weather Dashboard - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        weather_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("weather")
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

        # Weather Summary Section
        st.markdown("### 🌤️ Current Weather Summary")
        
        if not df.empty:
            latest = df.iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                temp = latest.get('temperature', 'N/A')
                st.metric("🌡️ Temperature", f"{temp}°C" if temp != 'N/A' else 'N/A')
            with col2:
                humidity = latest.get('humidity', 'N/A')
                st.metric("💧 Humidity", f"{humidity}%" if humidity != 'N/A' else 'N/A')
            with col3:
                wind = latest.get('wind_speed', 'N/A')
                st.metric("💨 Wind Speed", f"{wind} m/s" if wind != 'N/A' else 'N/A')
            with col4:
                city = latest.get('city_name', 'N/A')
                st.metric("🏙️ Location", city)

            # Weather description
            description = latest.get('description', 'No description available')
            st.info(f"**Current Condition:** {description}")

        # Weather Statistics
        st.markdown("### 📊 Weather Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Records", len(df))
        with col2:
            if "temperature" in df.columns:
                avg_temp = df['temperature'].mean()
                st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C")
        with col3:
            if "humidity" in df.columns:
                avg_humidity = df['humidity'].mean()
                st.metric("💧 Avg Humidity", f"{avg_humidity:.1f}%")
        with col4:
            if "city_name" in df.columns:
                unique_cities = df["city_name"].nunique()
                st.metric("🏙️ Cities Tracked", unique_cities)

        # Weather extremes
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if "temperature" in df.columns:
                max_temp = df['temperature'].max()
                st.metric("🔥 Max Temperature", f"{max_temp}°C")
        with col2:
            if "temperature" in df.columns:
                min_temp = df['temperature'].min()
                st.metric("🧊 Min Temperature", f"{min_temp}°C")
        with col3:
            if "wind_speed" in df.columns:
                max_wind = df['wind_speed'].max()
                st.metric("💨 Max Wind Speed", f"{max_wind} m/s")
        with col4:
            if "humidity" in df.columns:
                max_humidity = df['humidity'].max()
                st.metric("💧 Max Humidity", f"{max_humidity}%")

        # Weather trends charts
        st.markdown("### 📈 Weather Trends")
        
        # Temperature and humidity over time
        if "temperature" in df.columns and "humidity" in df.columns:
            fig = go.Figure()
            
            # Temperature line
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['temperature'],
                mode='lines+markers',
                name='Temperature (°C)',
                line=dict(color='red'),
                yaxis='y'
            ))
            
            # Humidity line (secondary y-axis)
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['humidity'],
                mode='lines+markers',
                name='Humidity (%)',
                line=dict(color='blue'),
                yaxis='y2'
            ))
            
            # Update layout for dual y-axis
            fig.update_layout(
                title="Temperature and Humidity Over Time",
                xaxis_title="Time",
                yaxis=dict(title="Temperature (°C)", side="left"),
                yaxis2=dict(title="Humidity (%)", side="right", overlaying="y"),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

        # Wind speed chart
        if "wind_speed" in df.columns:
            fig_wind = px.line(df, x='timestamp', y='wind_speed',
                             title="Wind Speed Over Time",
                             labels={'wind_speed': 'Wind Speed (m/s)', 'timestamp': 'Time'})
            st.plotly_chart(fig_wind, use_container_width=True)

        # Weather condition distribution
        if "description" in df.columns:
            condition_counts = df['description'].value_counts().head(10)
            fig_conditions = px.bar(
                x=condition_counts.values,
                y=condition_counts.index,
                orientation='h',
                title="Weather Conditions Distribution",
                labels={'x': 'Count', 'y': 'Weather Condition'}
            )
            fig_conditions.update_layout(height=400)
            st.plotly_chart(fig_conditions, use_container_width=True)

        # Display weather data table
        st.markdown("### 📋 Weather Records")
        display_columns = ["timestamp", "city_name", "description", "temperature", "humidity", "wind_speed"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            display_df = df[available_columns].copy()
            display_df.columns = ["Time", "City", "Description", "Temperature (°C)", "Humidity (%)", "Wind Speed (m/s)"]
            display_df["Time"] = display_df["Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_df, use_container_width=True)
        else:
            display_df = df.copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

        # Weather insights
        with st.expander("🔍 Weather Insights"):
            st.markdown("#### 📊 Key Insights:")
            
            if "temperature" in df.columns:
                temp_trend = "increasing" if df['temperature'].iloc[0] > df['temperature'].iloc[-1] else "decreasing"
                st.write(f"• **Temperature Trend:** {temp_trend.title()} over the recorded period")
            
            if "humidity" in df.columns:
                humid_trend = "increasing" if df['humidity'].iloc[0] > df['humidity'].iloc[-1] else "decreasing"
                st.write(f"• **Humidity Trend:** {humid_trend.title()} over the recorded period")
            
            if "description" in df.columns:
                most_common = df['description'].mode().iloc[0] if not df['description'].mode().empty else "Unknown"
                st.write(f"• **Most Common Weather:** {most_common}")
            
            # Data quality info
            st.write(f"• **Data Coverage:** {len(df)} weather records")
            if not df.empty:
                time_span = df['timestamp'].max() - df['timestamp'].min()
                st.write(f"• **Time Span:** {time_span.days} days, {time_span.seconds//3600} hours")

    except Exception as e:
        st.error(f"❌ Error loading weather data: {str(e)}")

def main():
    """Main application logic with Firebase role-based access control"""
    
    # Initialize session state for admin dashboard
    if "show_admin_dashboard" not in st.session_state:
        st.session_state.show_admin_dashboard = False
    
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
    .access-denied {
        background: #ffebee;
        border: 1px solid #f44336;
        padding: 1rem;
        border-radius: 5px;
        color: #d32f2f;
        margin: 1rem 0;
    }
    .permission-info {
        background: #e3f2fd;
        border: 1px solid #2196f3;
        padding: 1rem;
        border-radius: 5px;
        color: #1976d2;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # App header
    st.markdown('<div class="main-header"><h1>🛡️ Guardian Dashboard</h1><p>Real-time Device Monitoring & Analytics</p></div>', unsafe_allow_html=True)

    # Authentication check
    if not login():
        st.info("👆 Please log in to access the dashboard")
        return

    # Initialize Firebase and Role Manager
    db = init_firebase()
    role_manager = FirebaseRoleManager(db)
    
    current_user_email = st.session_state.email
    
    # Initialize system if this is the first super admin login
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
    if current_user_email.lower() == super_admin_email.lower():
        role_manager.initialize_system(current_user_email)
    
    # Get user location info for login logging
    location_info = get_user_location_info()
    user_agent = "Streamlit App"  # Since we can't easily get user agent in Streamlit
    
    # Log user login with notification
    role_manager.log_user_login(
        current_user_email, 
        location_info["ip"], 
        user_agent, 
        location_info["location"]
    )

    # Check if user exists in system
    user_profile = role_manager.get_user_profile(current_user_email)
    
    if not user_profile:
        st.error("🚫 Access Denied: Your account is not registered in the system.")
        st.info("Please contact the administrator to set up your account.")
        return
    
    if not user_profile.get("is_active", False):
        st.error("🚫 Access Denied: Your account has been deactivated.")
        st.info("Please contact the administrator for assistance.")
        return

    # Show user role information in sidebar
    st.sidebar.markdown("### 🔐 Access Information")
    if role_manager.is_super_admin(current_user_email):
        st.sidebar.success("👑 Super Administrator")
        st.sidebar.info("✅ Full system access")
        
        # Add admin dashboard option
        if st.sidebar.button("🛠️ Admin Dashboard"):
            st.session_state.show_admin_dashboard = True
            st.rerun()
        
        # Check if admin dashboard should be shown
        if st.session_state.get("show_admin_dashboard", False):
            show_admin_dashboard(db, current_user_email)
            
            if st.sidebar.button("📊 Back to Main Dashboard"):
                st.session_state.show_admin_dashboard = False
                st.rerun()
            return
    else:
        st.sidebar.info(f"👤 User\n📧 {current_user_email}")
        permissions = user_profile.get("permissions", {})
        st.sidebar.write("**Your Permissions:**")
        for perm, granted in permissions.items():
            if granted:
                st.sidebar.write(f"✅ {perm.replace('_', ' ').title()}")

    # User and device selection
    selected_user, selected_device = show_user_device_selector(role_manager, current_user_email)
    
    if not selected_user or not selected_device:
        st.warning("⚠️ Please select a user and device to continue")
        return

    # Sidebar navigation with permission-based filtering
    st.sidebar.markdown("---")
    st.sidebar.title("📊 Navigation")
    
    # Build available pages based on permissions
    all_pages = {
        "📱 Device Overview": ("device_overview", show_device_overview),
        "🌍 Location Tracker": ("locations", show_locations),
        "🌦️ Weather Dashboard": ("weather", show_weather),
        "📞 Call Logs": ("call_logs", show_call_logs),
        "👥 Contacts": ("contacts", show_contacts),
        "💬 Messages": ("messages", show_messages),
        "📶 Phone State": ("phone_state", show_phone_state)
    }
    
    available_pages = {}
    for page_name, (permission, function) in all_pages.items():
        if role_manager.can_access_feature(current_user_email, permission):
            available_pages[page_name] = function
    
    if not available_pages:
        st.error("🚫 No features available for your account. Please contact administrator.")
        return
    
    selected_page = st.sidebar.selectbox(
        "Choose a section:",
        list(available_pages.keys()),
        index=0
    )
    
    # User info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(f"🔐 Logged in as:\n{current_user_email}")
    
    if st.sidebar.button("🚪 Logout"):
        # Log logout
        role_manager.log_audit_event("user_logout", current_user_email, {
            "ip_address": location_info["ip"],
            "location": location_info["location"]
        })
        
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Display selected page
    try:
        # Log feature access
        feature_name = [k for k, v in all_pages.items() if v[1] == available_pages[selected_page]][0]
        permission_name = [v[0] for k, v in all_pages.items() if k == feature_name][0]
        role_manager.log_audit_event("feature_accessed", current_user_email, {
            "feature": permission_name,
            "target_user": selected_user,
            "device": selected_device
        })
        
        # Call the selected page function
        available_pages[selected_page](role_manager, selected_user, selected_device)
        
    except Exception as e:
        st.error(f"❌ Error loading {selected_page}: {str(e)}")
        st.info("This might be due to missing data or network issues. Please try refreshing the page.")

if __name__ == "__main__":
    main()