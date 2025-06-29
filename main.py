# main.py – Complete Enhanced Guardian Dashboard with Comprehensive Monitoring

import streamlit as st
from auth import login
from firebase_admin import credentials, firestore, initialize_app
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

/* Enhanced styling for better UI */
.main-header {
    text-align: center;
    padding: 1.5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.metric-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.status-active {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    color: #2d5016;
    padding: 0.5rem;
    border-radius: 8px;
    text-align: center;
}

.status-inactive {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    color: #8b4513;
    padding: 0.5rem;
    border-radius: 8px;
    text-align: center;
}

.feature-section {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    border-left: 4px solid #007bff;
}

.audio-transcription {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.device-monitoring {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}
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

# Enhanced Helper Functions
def format_duration(seconds):
    """Convert seconds to minutes and seconds format"""
    if pd.isna(seconds) or seconds == 0:
        return "0m 0s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if pd.isna(bytes_value) or bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_call_type_name(call_type):
    """Convert call type number to readable name with icons"""
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
    """Convert message type number to readable name with icons"""
    message_types = {
        1: "📥 Received",
        2: "📤 Sent",
        3: "📝 Draft", 
        4: "📤 Outbox",
        5: "❌ Failed",
        6: "⏳ Queued"
    }
    return message_types.get(msg_type, f"❓ Unknown ({msg_type})")

def get_app_category_icon(app_name):
    """Get category icon for app based on name"""
    app_name_lower = app_name.lower()
    
    if any(social in app_name_lower for social in ['whatsapp', 'facebook', 'instagram', 'twitter', 'telegram', 'snapchat']):
        return "💬"
    elif any(game in app_name_lower for game in ['game', 'play', 'puzzle', 'casino']):
        return "🎮"
    elif any(media in app_name_lower for media in ['youtube', 'netflix', 'spotify', 'music', 'video']):
        return "🎵"
    elif any(work in app_name_lower for work in ['office', 'word', 'excel', 'powerpoint', 'teams', 'slack']):
        return "💼"
    elif any(browser in app_name_lower for browser in ['chrome', 'firefox', 'browser', 'edge']):
        return "🌐"
    elif any(shopping in app_name_lower for shopping in ['amazon', 'flipkart', 'shopping', 'store']):
        return "🛒"
    elif any(travel in app_name_lower for travel in ['maps', 'uber', 'ola', 'travel']):
        return "🗺️"
    elif any(finance in app_name_lower for finance in ['bank', 'pay', 'wallet', 'finance']):
        return "💳"
    else:
        return "📱"

def get_user_location_info():
    """Get user's location information"""
    try:
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
            
            # Show device info in selection
            device_options = []
            for device_id in device_ids:
                device_info = device_map[device_id]
                device_name = device_info.get('device', 'Unknown Device')
                brand = device_info.get('brand', 'Unknown')
                device_options.append(f"{device_name} ({brand}) - {device_id[:8]}...")
            
            if len(device_options) == 1:
                selected_device = device_ids[0]
                st.sidebar.info(f"📱 Device: {device_options[0]}")
            else:
                selected_idx = st.sidebar.selectbox(
                    "📱 Select Device",
                    range(len(device_options)),
                    format_func=lambda x: device_options[x],
                    key="device_selector"
                )
                selected_device = device_ids[selected_idx]
            
            return selected_user, selected_device
            
        except Exception as e:
            st.sidebar.error(f"Error fetching devices: {str(e)}")
            return selected_user, None
    
    return None, None

# Enhanced Page Functions with Comprehensive Monitoring
def show_device_overview(role_manager, selected_user, selected_device):
    """Enhanced device overview with comprehensive monitoring"""
    if not role_manager.can_access_feature(st.session_state.email, "device_overview"):
        st.error("🚫 Access Denied: You don't have permission to view device overview")
        return
    
    st.markdown('<div class="feature-section">', unsafe_allow_html=True)
    st.subheader(f"📱 Comprehensive Device Overview - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        device_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device)
        device_doc = device_ref.get()
        
        if not device_doc.exists:
            st.warning("⚠️ Device not found.")
            return
        
        device = device_doc.to_dict()

        # Device Status Overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            is_active = device.get('isActive', False)
            if is_active:
                st.markdown('<div class="status-active">🟢 Active Device</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-inactive">🔴 Inactive Device</div>', unsafe_allow_html=True)
        
        with col2:
            last_sync = device.get('lastSyncTime', 'Never')
            if last_sync != 'Never':
                try:
                    last_sync_dt = datetime.fromtimestamp(last_sync / 1000.0)
                    time_diff = datetime.now() - last_sync_dt
                    if time_diff.total_seconds() < 3600:  # Less than 1 hour
                        st.success(f"🔄 Last Sync: {last_sync_dt.strftime('%H:%M')}")
                    else:
                        st.warning(f"⚠️ Last Sync: {last_sync_dt.strftime('%m/%d %H:%M')}")
                except:
                    st.info(f"🔄 Last Sync: {last_sync}")
            else:
                st.error("❌ Never Synced")
        
        with col3:
            android_version = device.get('androidVersion', 'Unknown')
            api_level = device.get('apiLevel', 'Unknown')
            st.info(f"🤖 Android {android_version}\nAPI {api_level}")
        
        with col4:
            battery_level = device.get('batteryLevel', 'Unknown')
            if isinstance(battery_level, (int, float)):
                if battery_level > 50:
                    st.success(f"🔋 Battery: {battery_level}%")
                elif battery_level > 20:
                    st.warning(f"🔋 Battery: {battery_level}%")
                else:
                    st.error(f"🔋 Battery: {battery_level}%")
            else:
                st.info(f"🔋 Battery: {battery_level}")

        st.markdown("### 📊 Device Hardware Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📱 Device Model", device.get('device', 'Unknown'))
            st.metric("🏭 Brand", device.get('brand', 'Unknown'))
            st.metric("🏗️ Manufacturer", device.get('manufacturer', 'Unknown'))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🔧 Hardware", device.get('hardware', 'Unknown'))
            st.metric("🆔 Build ID", device.get('buildId', 'Unknown')[:15] + "..." if device.get('buildId') else 'Unknown')
            st.metric("📡 Network Operator", device.get('networkOperatorName', 'Unknown'))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📞 Device ID", device.get('deviceId', 'Unknown')[:15] + "..." if device.get('deviceId') else 'Unknown')
            st.metric("📶 IMEI", device.get('imei', 'Unknown')[:10] + "..." if device.get('imei') else 'Unknown')
            st.metric("📋 Serial Number", device.get('serialNumber', 'Unknown')[:10] + "..." if device.get('serialNumber') else 'Unknown')
            st.markdown('</div>', unsafe_allow_html=True)

        # Memory and Storage Information
        st.markdown("### 💾 System Resources")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_memory = device.get('totalMemory', 0)
            if total_memory:
                st.metric("💾 Total RAM", format_bytes(total_memory))
            else:
                st.metric("💾 Total RAM", "Unknown")
        
        with col2:
            available_memory = device.get('availableMemory', 0)
            if available_memory:
                st.metric("🆓 Available RAM", format_bytes(available_memory))
            else:
                st.metric("🆓 Available RAM", "Unknown")
        
        with col3:
            total_storage = device.get('totalStorage', 0)
            if total_storage:
                st.metric("💿 Total Storage", format_bytes(total_storage))
            else:
                st.metric("💿 Total Storage", "Unknown")
        
        with col4:
            available_storage = device.get('availableStorage', 0)
            if available_storage:
                st.metric("🆓 Available Storage", format_bytes(available_storage))
            else:
                st.metric("🆓 Available Storage", "Unknown")

        # Display and Hardware Features
        st.markdown("### 📱 Display & Features")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            screen_width = device.get('screenWidth', 'Unknown')
            screen_height = device.get('screenHeight', 'Unknown')
            st.metric("📐 Screen Resolution", f"{screen_width}x{screen_height}")
        
        with col2:
            density = device.get('density', 'Unknown')
            st.metric("🔍 Screen Density", f"{density} dpi" if density != 'Unknown' else 'Unknown')
        
        with col3:
            cpu_cores = device.get('cpuCores', 'Unknown')
            st.metric("⚙️ CPU Cores", cpu_cores)
        
        with col4:
            has_bluetooth = device.get('hasBluetooth', False)
            st.metric("📡 Bluetooth", "✅ Available" if has_bluetooth else "❌ Not Available")

        # Security and Permissions Status
        st.markdown("### 🔐 Security & Permissions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            root_access = device.get('isRooted', False)
            if root_access:
                st.error("🔓 Device is Rooted")
            else:
                st.success("🔒 Device Not Rooted")
        
        with col2:
            developer_options = device.get('developerOptionsEnabled', False)
            if developer_options:
                st.warning("⚡ Developer Options Enabled")
            else:
                st.success("🔐 Developer Options Disabled")
        
        with col3:
            unknown_sources = device.get('unknownSourcesEnabled', False)
            if unknown_sources:
                st.warning("📦 Unknown Sources Enabled")
            else:
                st.success("🛡️ Unknown Sources Disabled")

        # Comprehensive Data Collections Status
        st.markdown("### 📊 Data Collection Status")
        
        # Get collection stats
        collections_to_check = [
            ("locations", "🌍 Location Data"),
            ("call_logs", "📞 Call Logs"),
            ("messages", "💬 Messages"),
            ("contacts", "👥 Contacts"),
            ("audio_recordings", "🎙️ Audio Recordings"),
            ("weather", "🌦️ Weather Data"),
            ("installed_apps", "📱 Installed Apps"),
            ("app_usage", "📊 App Usage"),
            ("battery_status", "🔋 Battery Status"),
            ("system_metrics", "🖥️ System Metrics"),
            ("sensor_data", "📡 Sensor Data"),
            ("phone_state", "📶 Phone State")
        ]
        
        col1, col2, col3, col4 = st.columns(4)
        collections_per_col = len(collections_to_check) // 4 + 1
        
        for idx, (collection_name, display_name) in enumerate(collections_to_check):
            col_idx = idx // collections_per_col
            current_col = [col1, col2, col3, col4][col_idx]
            
            try:
                collection_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection(collection_name)
                docs = list(collection_ref.limit(1).stream())
                
                if docs:
                    # Get document count
                    count_query = collection_ref.count()
                    count_result = count_query.get()
                    doc_count = count_result[0][0].value if count_result else 0
                    
                    current_col.success(f"{display_name}\n📊 {doc_count} records")
                else:
                    current_col.info(f"{display_name}\n📊 No data")
            except:
                current_col.error(f"{display_name}\n❌ Error")

        # Recent Activity Summary
        st.markdown("### 🕐 Recent Activity Summary")
        
        try:
            # Get recent data from various collections
            recent_activity = []
            
            for collection_name, display_name in collections_to_check[:6]:  # Check first 6 collections
                try:
                    collection_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection(collection_name)
                    recent_docs = collection_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
                    
                    for doc in recent_docs:
                        data = doc.to_dict()
                        timestamp = data.get('timestamp', 0)
                        if timestamp:
                            dt = datetime.fromtimestamp(timestamp / 1000.0)
                            recent_activity.append({
                                'collection': display_name,
                                'timestamp': dt,
                                'time_ago': datetime.now() - dt
                            })
                except:
                    continue
            
            if recent_activity:
                recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
                
                st.markdown("**Last Activity:**")
                for activity in recent_activity[:5]:
                    time_ago = activity['time_ago']
                    if time_ago.days > 0:
                        time_str = f"{time_ago.days} days ago"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds // 3600} hours ago"
                    else:
                        time_str = f"{time_ago.seconds // 60} minutes ago"
                    
                    st.write(f"• {activity['collection']}: {time_str}")
            else:
                st.info("No recent activity found")
                
        except Exception as e:
            st.warning(f"Could not load recent activity: {str(e)}")

        # Detailed Device Information
        with st.expander("🔍 Complete Device Information"):
            st.json(device)

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading device overview: {str(e)}")

def show_audio_recordings(role_manager, selected_user, selected_device):
    """Enhanced audio recordings with transcription support"""
    if not role_manager.can_access_feature(st.session_state.email, "audio_recordings"):
        st.error("🚫 Access Denied: You don't have permission to view audio recordings")
        return
    
    st.markdown('<div class="audio-transcription">', unsafe_allow_html=True)
    st.subheader(f"🎙️ Audio Recordings & Transcription - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        audio_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("audio_recordings")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            transcription_filter = st.selectbox("🎯 Filter by", ["All", "Transcribed", "Pending", "Failed"])

        # Get audio recordings
        audio_docs = audio_ref.order_by("startTime", direction=firestore.Query.DESCENDING).limit(1000).stream()
        
        audio_data = []
        for doc in audio_docs:
            entry = doc.to_dict()
            start_time = entry.get("startTime", 0)
            if start_time:
                entry["start_datetime"] = datetime.fromtimestamp(start_time / 1000.0)
                entry["duration_formatted"] = format_duration(entry.get("duration", 0) / 1000.0)
                entry["file_size_formatted"] = format_bytes(entry.get("fileSize", 0))
                audio_data.append(entry)

        if not audio_data:
            st.info("🎙️ No audio recordings found for this device.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(audio_data)
        
        # Filter by date
        if selected_date:
            df = df[df["start_datetime"].dt.date == selected_date]
        
        # Filter by transcription status
        if transcription_filter != "All":
            status_map = {
                "Transcribed": "COMPLETED",
                "Pending": "PENDING", 
                "Failed": "FAILED"
            }
            df = df[df["transcriptionStatus"] == status_map[transcription_filter]]

        if df.empty:
            st.info(f"🎙️ No audio recordings found for {selected_date} with status '{transcription_filter}'")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Audio Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎙️ Total Recordings", len(df))
        with col2:
            total_duration = df["duration"].sum() / 1000.0  # Convert to seconds
            st.metric("⏱️ Total Duration", format_duration(total_duration))
        with col3:
            total_size = df["fileSize"].sum()
            st.metric("💾 Total Size", format_bytes(total_size))
        with col4:
            transcribed_count = len(df[df["transcriptionStatus"] == "COMPLETED"])
            st.metric("✅ Transcribed", f"{transcribed_count}/{len(df)}")

        # Transcription Status Overview
        st.markdown("### 📊 Transcription Status")
        status_counts = df["transcriptionStatus"].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Transcription Status Distribution"
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Language distribution
            if "transcriptionLanguage" in df.columns:
                lang_counts = df["transcriptionLanguage"].value_counts()
                fig_lang = px.bar(
                    x=lang_counts.values,
                    y=lang_counts.index,
                    orientation='h',
                    title="Transcription Languages"
                )
                st.plotly_chart(fig_lang, use_container_width=True)

        # Audio Recordings Table
        st.markdown("### 🎵 Recording Details")
        
        for idx, row in df.iterrows():
            with st.expander(f"🎙️ Recording {row.get('fileName', 'Unknown')} - {row['start_datetime'].strftime('%H:%M:%S')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**📅 Date:** {row['start_datetime'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**⏱️ Duration:** {row['duration_formatted']}")
                    st.write(f"**💾 File Size:** {row['file_size_formatted']}")
                
                with col2:
                    status = row.get("transcriptionStatus", "Unknown")
                    if status == "COMPLETED":
                        st.success(f"**✅ Status:** {status}")
                    elif status == "PENDING":
                        st.warning(f"**⏳ Status:** {status}")
                    else:
                        st.error(f"**❌ Status:** {status}")
                    
                    confidence = row.get("transcriptionConfidence", 0)
                    if confidence > 0:
                        st.write(f"**🎯 Confidence:** {confidence:.2f}")
                    
                    language = row.get("transcriptionLanguage", "Unknown")
                    st.write(f"**🌐 Language:** {language}")
                
                with col3:
                    uploaded = row.get("uploadedToCloud", False)
                    if uploaded:
                        st.success("☁️ **Uploaded to Cloud**")
                    else:
                        st.info("📱 **Local Storage Only**")
                
                # Display transcription if available
                transcription = row.get("transcription", "")
                if transcription and transcription.strip():
                    st.markdown("**📝 Transcription:**")
                    st.text_area("", transcription, height=100, key=f"transcription_{idx}")
                else:
                    st.info("📝 No transcription available")

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading audio recordings: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_installed_apps(role_manager, selected_user, selected_device):
    """Show installed apps with enhanced analytics"""
    if not role_manager.can_access_feature(st.session_state.email, "installed_apps"):
        st.error("🚫 Access Denied: You don't have permission to view installed apps")
        return
    
    st.markdown('<div class="device-monitoring">', unsafe_allow_html=True)
    st.subheader(f"📱 Installed Applications - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        apps_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("installed_apps")
        
        # Get apps data
        apps_docs = apps_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1000).stream()
        
        apps_data = []
        for doc in apps_docs:
            entry = doc.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            entry["app_icon"] = get_app_category_icon(entry.get("appName", ""))
            apps_data.append(entry)

        if not apps_data:
            st.info("📱 No installed apps data found.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(apps_data)
        
        # App Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📱 Total Apps", len(df))
        with col2:
            system_apps = len(df[df.get("isSystemApp", False) == True])
            st.metric("⚙️ System Apps", system_apps)
        with col3:
            user_apps = len(df[df.get("isSystemApp", False) == False])
            st.metric("👤 User Apps", user_apps)
        with col4:
            if "lastUpdateTime" in df.columns:
                recent_updates = len(df[df["lastUpdateTime"] > (datetime.now() - timedelta(days=30)).timestamp() * 1000])
                st.metric("🔄 Recent Updates", recent_updates)

        # App Categories
        st.markdown("### 📊 App Categories")
        
        # Create category distribution
        category_counts = df["app_icon"].value_counts()
        category_names = {
            "💬": "Social & Communication",
            "🎮": "Games & Entertainment", 
            "🎵": "Media & Entertainment",
            "💼": "Productivity & Work",
            "🌐": "Browsers & Web",
            "🛒": "Shopping & Commerce",
            "🗺️": "Maps & Travel",
            "💳": "Finance & Banking",
            "📱": "Other Apps"
        }
        
        col1, col2 = st.columns(2)
        with col1:
            # Category pie chart
            display_names = [category_names.get(cat, cat) for cat in category_counts.index]
            fig_categories = px.pie(
                values=category_counts.values,
                names=display_names,
                title="App Category Distribution"
            )
            st.plotly_chart(fig_categories, use_container_width=True)
        
        with col2:
            # System vs User apps
            system_user_counts = df.groupby(df.get("isSystemApp", False)).size()
            fig_type = px.bar(
                x=["User Apps", "System Apps"],
                y=[system_user_counts.get(False, 0), system_user_counts.get(True, 0)],
                title="System vs User Apps"
            )
            st.plotly_chart(fig_type, use_container_width=True)

        # Search and filter
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("🔍 Search apps")
        with col2:
            app_type_filter = st.selectbox("Filter by type", ["All", "User Apps", "System Apps"])

        # Apply filters
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df["appName"].str.contains(search_term, case=False, na=False)]
        
        if app_type_filter == "User Apps":
            filtered_df = filtered_df[filtered_df.get("isSystemApp", False) == False]
        elif app_type_filter == "System Apps":
            filtered_df = filtered_df[filtered_df.get("isSystemApp", False) == True]

        # Apps Table
        st.markdown("### 📋 Applications List")
        
        if not filtered_df.empty:
            display_columns = ["app_icon", "appName", "packageName", "version", "isSystemApp"]
            available_columns = [col for col in display_columns if col in filtered_df.columns]
            
            if available_columns:
                display_df = filtered_df[available_columns].copy()
                display_df.columns = ["Category", "App Name", "Package Name", "Version", "System App"]
                display_df["System App"] = display_df["System App"].map({True: "✅", False: "❌"})
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No apps found matching your criteria")

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading installed apps: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_app_usage(role_manager, selected_user, selected_device):
    """Show app usage statistics with analytics"""
    if not role_manager.can_access_feature(st.session_state.email, "app_usage"):
        st.error("🚫 Access Denied: You don't have permission to view app usage")
        return
    
    st.markdown('<div class="device-monitoring">', unsafe_allow_html=True)
    st.subheader(f"📊 App Usage Analytics - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        usage_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("app_usage")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            days_range = st.selectbox("📅 Date Range", [1, 7, 30], index=0, format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}")

        # Calculate date range
        end_date = selected_date
        start_date = end_date - timedelta(days=days_range-1)
        
        start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
        end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
        
        # Get usage data
        usage_docs = usage_ref.where("timestamp", ">=", start_timestamp).where("timestamp", "<=", end_timestamp).stream()
        
        usage_data = []
        for doc in usage_docs:
            entry = doc.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            entry["usage_duration_formatted"] = format_duration(entry.get("usageTime", 0) / 1000.0)
            entry["app_icon"] = get_app_category_icon(entry.get("packageName", ""))
            usage_data.append(entry)

        if not usage_data:
            st.info(f"📊 No app usage data found for the selected period.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(usage_data)
        
        # Usage Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_apps = df["packageName"].nunique()
            st.metric("📱 Apps Used", total_apps)
        with col2:
            total_time = df["usageTime"].sum() / (1000 * 3600)  # Convert to hours
            st.metric("⏰ Total Usage", f"{total_time:.1f} hours")
        with col3:
            avg_daily = total_time / days_range
            st.metric("📅 Daily Average", f"{avg_daily:.1f} hours")
        with col4:
            most_used = df.groupby("packageName")["usageTime"].sum().idxmax()
            st.metric("🥇 Most Used", most_used.split('.')[-1])

        # Top Apps Chart
        st.markdown("### 🏆 Top Applications by Usage")
        
        app_totals = df.groupby("packageName")["usageTime"].sum().sort_values(ascending=False).head(10)
        app_totals_hours = app_totals / (1000 * 3600)  # Convert to hours
        
        col1, col2 = st.columns(2)
        with col1:
            fig_top_apps = px.bar(
                x=app_totals_hours.values,
                y=[pkg.split('.')[-1] for pkg in app_totals_hours.index],
                orientation='h',
                title="Top 10 Apps by Usage Time",
                labels={'x': 'Usage Time (hours)', 'y': 'App'}
            )
            st.plotly_chart(fig_top_apps, use_container_width=True)
        
        with col2:
            # Usage by category
            category_usage = df.groupby("app_icon")["usageTime"].sum() / (1000 * 3600)
            category_names = {
                "💬": "Social", "🎮": "Games", "🎵": "Media", "💼": "Work",
                "🌐": "Browser", "🛒": "Shopping", "🗺️": "Maps", "💳": "Finance", "📱": "Other"
            }
            
            display_names = [category_names.get(cat, cat) for cat in category_usage.index]
            fig_categories = px.pie(
                values=category_usage.values,
                names=display_names,
                title="Usage by Category"
            )
            st.plotly_chart(fig_categories, use_container_width=True)

        # Daily Usage Trend
        if days_range > 1:
            st.markdown("### 📈 Daily Usage Trend")
            daily_usage = df.groupby(df["timestamp"].dt.date)["usageTime"].sum() / (1000 * 3600)
            
            fig_daily = px.line(
                x=daily_usage.index,
                y=daily_usage.values,
                title="Daily Total Usage",
                labels={'x': 'Date', 'y': 'Usage Time (hours)'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)

        # Detailed Usage Table
        st.markdown("### 📋 Detailed Usage Data")
        
        # Aggregate by app
        app_summary = df.groupby("packageName").agg({
            "usageTime": "sum",
            "timestamp": "count"
        }).rename(columns={"timestamp": "sessions"})
        
        app_summary["usage_hours"] = app_summary["usageTime"] / (1000 * 3600)
        app_summary["avg_session"] = app_summary["usageTime"] / app_summary["sessions"] / (1000 * 60)  # minutes
        app_summary = app_summary.sort_values("usageTime", ascending=False)
        
        display_df = pd.DataFrame({
            "App Name": [pkg.split('.')[-1] for pkg in app_summary.index],
            "Total Usage (hours)": app_summary["usage_hours"].round(2),
            "Sessions": app_summary["sessions"],
            "Avg Session (min)": app_summary["avg_session"].round(1)
        })
        
        st.dataframe(display_df, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading app usage data: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_battery_status(role_manager, selected_user, selected_device):
    """Show battery status and health monitoring"""
    if not role_manager.can_access_feature(st.session_state.email, "battery_status"):
        st.error("🚫 Access Denied: You don't have permission to view battery status")
        return
    
    st.markdown('<div class="device-monitoring">', unsafe_allow_html=True)
    st.subheader(f"🔋 Battery Health & Monitoring - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        battery_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("battery_status")
        
        # Get battery data
        battery_docs = battery_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1000).stream()
        
        battery_data = []
        for doc in battery_docs:
            entry = doc.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            battery_data.append(entry)

        if not battery_data:
            st.info("🔋 No battery data found.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(battery_data)
        df = df.sort_values("timestamp", ascending=False)

        # Current Battery Status
        if not df.empty:
            latest = df.iloc[0]
            
            st.markdown("### 🔋 Current Battery Status")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                level = latest.get("batteryLevel", 0)
                if level > 80:
                    st.success(f"🔋 Level: {level}%")
                elif level > 20:
                    st.warning(f"🔋 Level: {level}%")
                else:
                    st.error(f"🔋 Level: {level}%")
            
            with col2:
                is_charging = latest.get("isCharging", False)
                if is_charging:
                    st.success("⚡ Charging")
                else:
                    st.info("🔌 Not Charging")
            
            with col3:
                temperature = latest.get("temperature", 0) / 10.0  # Convert to Celsius
                if temperature > 40:
                    st.error(f"🌡️ {temperature:.1f}°C (Hot!)")
                elif temperature > 35:
                    st.warning(f"🌡️ {temperature:.1f}°C (Warm)")
                else:
                    st.success(f"🌡️ {temperature:.1f}°C")
            
            with col4:
                health = latest.get("health", "Unknown")
                health_map = {
                    2: "✅ Good",
                    3: "⚠️ Overheat", 
                    4: "❌ Dead",
                    5: "🔄 Over Voltage",
                    6: "❌ Failure"
                }
                health_display = health_map.get(health, f"❓ {health}")
                if health == 2:
                    st.success(f"❤️ {health_display}")
                else:
                    st.warning(f"❤️ {health_display}")

        # Battery Statistics
        st.markdown("### 📊 Battery Analytics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_level = df["batteryLevel"].mean()
            st.metric("📊 Average Level", f"{avg_level:.1f}%")
        
        with col2:
            charging_time = len(df[df.get("isCharging", False) == True])
            total_time = len(df)
            charging_pct = (charging_time / total_time * 100) if total_time > 0 else 0
            st.metric("⚡ Charging Time", f"{charging_pct:.1f}%")
        
        with col3:
            if "temperature" in df.columns:
                avg_temp = df["temperature"].mean() / 10.0
                st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C")
        
        with col4:
            if "voltage" in df.columns:
                avg_voltage = df["voltage"].mean() / 1000.0  # Convert to volts
                st.metric("⚡ Avg Voltage", f"{avg_voltage:.2f}V")

        # Battery Level Trend
        st.markdown("### 📈 Battery Level Trend")
        
        # Limit to recent data for better visualization
        recent_df = df.head(100).sort_values("timestamp")
        
        fig = go.Figure()
        
        # Battery level line
        fig.add_trace(go.Scatter(
            x=recent_df["timestamp"],
            y=recent_df["batteryLevel"],
            mode='lines+markers',
            name='Battery Level (%)',
            line=dict(color='green', width=2),
            fill='tonexty',
            fillcolor='rgba(0,255,0,0.1)'
        ))
        
        # Add charging periods
        charging_df = recent_df[recent_df.get("isCharging", False) == True]
        if not charging_df.empty:
            fig.add_trace(go.Scatter(
                x=charging_df["timestamp"],
                y=charging_df["batteryLevel"],
                mode='markers',
                name='Charging',
                marker=dict(color='orange', size=8, symbol='lightning')
            ))
        
        fig.update_layout(
            title="Battery Level Over Time",
            xaxis_title="Time",
            yaxis_title="Battery Level (%)",
            yaxis=dict(range=[0, 100]),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Temperature Analysis
        if "temperature" in df.columns:
            st.markdown("### 🌡️ Temperature Analysis")
            
            col1, col2 = st.columns(2)
            with col1:
                temp_celsius = recent_df["temperature"] / 10.0
                fig_temp = px.line(
                    x=recent_df["timestamp"],
                    y=temp_celsius,
                    title="Battery Temperature",
                    labels={'x': 'Time', 'y': 'Temperature (°C)'}
                )
                fig_temp.add_hline(y=40, line_dash="dash", line_color="red", annotation_text="High Temperature Threshold")
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with col2:
                # Temperature distribution
                fig_temp_dist = px.histogram(
                    x=temp_celsius,
                    nbins=20,
                    title="Temperature Distribution",
                    labels={'x': 'Temperature (°C)', 'y': 'Count'}
                )
                st.plotly_chart(fig_temp_dist, use_container_width=True)

        # Charging Analysis
        st.markdown("### ⚡ Charging Analysis")
        
        if "chargingSource" in df.columns:
            charging_sources = df["chargingSource"].value_counts()
            source_map = {
                1: "🔌 AC Charger",
                2: "💻 USB",
                4: "📱 Wireless"
            }
            
            source_display = {source_map.get(k, f"Unknown ({k})"): v for k, v in charging_sources.items()}
            
            fig_sources = px.pie(
                values=list(source_display.values()),
                names=list(source_display.keys()),
                title="Charging Source Distribution"
            )
            st.plotly_chart(fig_sources, use_container_width=True)

        # Battery Health Insights
        with st.expander("🔍 Battery Health Insights"):
            st.markdown("#### 🔋 Health Assessment:")
            
            if not df.empty:
                # Temperature analysis
                temp_data = df["temperature"] / 10.0 if "temperature" in df.columns else None
                if temp_data is not None:
                    high_temp_count = len(temp_data[temp_data > 40])
                    total_readings = len(temp_data)
                    high_temp_pct = (high_temp_count / total_readings * 100) if total_readings > 0 else 0
                    
                    if high_temp_pct > 10:
                        st.warning(f"⚠️ **Temperature Warning:** Device runs hot {high_temp_pct:.1f}% of the time")
                    else:
                        st.success(f"✅ **Temperature Normal:** Good thermal management")
                
                # Charging pattern analysis
                if "isCharging" in df.columns:
                    charging_sessions = []
                    current_session = None
                    
                    for _, row in df.sort_values("timestamp").iterrows():
                        if row.get("isCharging", False):
                            if current_session is None:
                                current_session = {"start": row["timestamp"], "start_level": row["batteryLevel"]}
                        else:
                            if current_session is not None:
                                current_session["end"] = row["timestamp"]
                                current_session["end_level"] = row["batteryLevel"]
                                charging_sessions.append(current_session)
                                current_session = None
                    
                    if charging_sessions:
                        avg_charge_time = np.mean([(s["end"] - s["start"]).total_seconds() / 3600 for s in charging_sessions])
                        st.info(f"📊 **Average Charging Time:** {avg_charge_time:.1f} hours")
                
                # Battery level patterns
                level_variance = df["batteryLevel"].var()
                if level_variance < 100:
                    st.success("✅ **Stable Usage:** Consistent battery drain pattern")
                else:
                    st.info("📊 **Variable Usage:** Battery usage varies significantly")

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading battery data: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_system_metrics(role_manager, selected_user, selected_device):
    """Show comprehensive system metrics and performance monitoring"""
    if not role_manager.can_access_feature(st.session_state.email, "system_metrics"):
        st.error("🚫 Access Denied: You don't have permission to view system metrics")
        return
    
    st.markdown('<div class="device-monitoring">', unsafe_allow_html=True)
    st.subheader(f"🖥️ System Performance Metrics - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        metrics_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("system_metrics")
        
        # Get system metrics data
        metrics_docs = metrics_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(500).stream()
        
        metrics_data = []
        for doc in metrics_docs:
            entry = doc.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            metrics_data.append(entry)

        if not metrics_data:
            st.info("🖥️ No system metrics data found.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(metrics_data)
        df = df.sort_values("timestamp", ascending=False)

        # Current System Status
        if not df.empty:
            latest = df.iloc[0]
            
            st.markdown("### 🖥️ Current System Status")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                available_memory = latest.get("availableMemory", 0)
                total_memory = latest.get("totalMemory", 1)
                memory_usage_pct = ((total_memory - available_memory) / total_memory * 100) if total_memory > 0 else 0
                
                if memory_usage_pct > 80:
                    st.error(f"💾 RAM: {memory_usage_pct:.1f}% used")
                elif memory_usage_pct > 60:
                    st.warning(f"💾 RAM: {memory_usage_pct:.1f}% used")
                else:
                    st.success(f"💾 RAM: {memory_usage_pct:.1f}% used")
            
            with col2:
                available_storage = latest.get("availableStorage", 0)
                total_storage = latest.get("totalStorage", 1)
                storage_usage_pct = ((total_storage - available_storage) / total_storage * 100) if total_storage > 0 else 0
                
                if storage_usage_pct > 90:
                    st.error(f"💿 Storage: {storage_usage_pct:.1f}% used")
                elif storage_usage_pct > 70:
                    st.warning(f"💿 Storage: {storage_usage_pct:.1f}% used")
                else:
                    st.success(f"💿 Storage: {storage_usage_pct:.1f}% used")
            
            with col3:
                cpu_usage = latest.get("cpuUsage", 0)
                if cpu_usage > 80:
                    st.error(f"⚙️ CPU: {cpu_usage:.1f}%")
                elif cpu_usage > 60:
                    st.warning(f"⚙️ CPU: {cpu_usage:.1f}%")
                else:
                    st.success(f"⚙️ CPU: {cpu_usage:.1f}%")
            
            with col4:
                network_strength = latest.get("networkStrength", 0)
                if network_strength > -70:
                    st.success(f"📶 Signal: Strong")
                elif network_strength > -85:
                    st.warning(f"📶 Signal: Fair")
                else:
                    st.error(f"📶 Signal: Weak")

        # Resource Usage Trends
        st.markdown("### 📈 Resource Usage Trends")
        
        # Limit to recent data for better visualization
        recent_df = df.head(100).sort_values("timestamp")
        
        # Memory and Storage Usage
        col1, col2 = st.columns(2)
        
        with col1:
            if "availableMemory" in recent_df.columns and "totalMemory" in recent_df.columns:
                memory_usage = ((recent_df["totalMemory"] - recent_df["availableMemory"]) / recent_df["totalMemory"] * 100)
                
                fig_memory = px.line(
                    x=recent_df["timestamp"],
                    y=memory_usage,
                    title="Memory Usage Over Time",
                    labels={'x': 'Time', 'y': 'Memory Usage (%)'}
                )
                fig_memory.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="High Usage")
                fig_memory.update_layout(yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_memory, use_container_width=True)
        
        with col2:
            if "availableStorage" in recent_df.columns and "totalStorage" in recent_df.columns:
                storage_usage = ((recent_df["totalStorage"] - recent_df["availableStorage"]) / recent_df["totalStorage"] * 100)
                
                fig_storage = px.line(
                    x=recent_df["timestamp"],
                    y=storage_usage,
                    title="Storage Usage Over Time",
                    labels={'x': 'Time', 'y': 'Storage Usage (%)'}
                )
                fig_storage.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Critical Level")
                fig_storage.update_layout(yaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_storage, use_container_width=True)

        # CPU and Network Performance
        col1, col2 = st.columns(2)
        
        with col1:
            if "cpuUsage" in recent_df.columns:
                fig_cpu = px.line(
                    x=recent_df["timestamp"],
                    y=recent_df["cpuUsage"],
                    title="CPU Usage Over Time",
                    labels={'x': 'Time', 'y': 'CPU Usage (%)'}
                )
                fig_cpu.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="High CPU")
                st.plotly_chart(fig_cpu, use_container_width=True)
        
        with col2:
            if "networkStrength" in recent_df.columns:
                fig_network = px.line(
                    x=recent_df["timestamp"],
                    y=recent_df["networkStrength"],
                    title="Network Signal Strength",
                    labels={'x': 'Time', 'y': 'Signal Strength (dBm)'}
                )
                fig_network.add_hline(y=-85, line_dash="dash", line_color="orange", annotation_text="Weak Signal")
                st.plotly_chart(fig_network, use_container_width=True)

        # System Resource Summary
        st.markdown("### 📊 Resource Utilization Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if "availableMemory" in df.columns and "totalMemory" in df.columns:
                avg_memory_usage = ((df["totalMemory"] - df["availableMemory"]) / df["totalMemory"] * 100).mean()
                st.metric("💾 Avg Memory Usage", f"{avg_memory_usage:.1f}%")
        
        with col2:
            if "availableStorage" in df.columns and "totalStorage" in df.columns:
                avg_storage_usage = ((df["totalStorage"] - df["availableStorage"]) / df["totalStorage"] * 100).mean()
                st.metric("💿 Avg Storage Usage", f"{avg_storage_usage:.1f}%")
        
        with col3:
            if "cpuUsage" in df.columns:
                avg_cpu = df["cpuUsage"].mean()
                st.metric("⚙️ Avg CPU Usage", f"{avg_cpu:.1f}%")
        
        with col4:
            if "networkStrength" in df.columns:
                avg_signal = df["networkStrength"].mean()
                signal_quality = "Strong" if avg_signal > -70 else "Fair" if avg_signal > -85 else "Weak"
                st.metric("📶 Signal Quality", signal_quality)

        # Performance Insights
        with st.expander("🔍 Performance Insights"):
            st.markdown("#### 🖥️ System Analysis:")
            
            if not df.empty:
                # Memory analysis
                if "availableMemory" in df.columns and "totalMemory" in df.columns:
                    memory_usage = ((df["totalMemory"] - df["availableMemory"]) / df["totalMemory"] * 100)
                    high_memory_count = len(memory_usage[memory_usage > 80])
                    total_readings = len(memory_usage)
                    high_memory_pct = (high_memory_count / total_readings * 100) if total_readings > 0 else 0
                    
                    if high_memory_pct > 20:
                        st.warning(f"⚠️ **Memory Pressure:** High usage detected {high_memory_pct:.1f}% of the time")
                    else:
                        st.success(f"✅ **Memory Normal:** Good memory management")
                
                # Storage analysis
                if "availableStorage" in df.columns and "totalStorage" in df.columns:
                    storage_usage = ((df["totalStorage"] - df["availableStorage"]) / df["totalStorage"] * 100)
                    latest_storage = storage_usage.iloc[0] if not storage_usage.empty else 0
                    
                    if latest_storage > 90:
                        st.error(f"🚨 **Storage Critical:** {latest_storage:.1f}% used - cleanup recommended")
                    elif latest_storage > 70:
                        st.warning(f"⚠️ **Storage Warning:** {latest_storage:.1f}% used")
                    else:
                        st.success(f"✅ **Storage Healthy:** {latest_storage:.1f}% used")
                
                # Performance trends
                if "cpuUsage" in df.columns:
                    cpu_trend = df["cpuUsage"].diff().mean()
                    if abs(cpu_trend) < 0.1:
                        st.info("📊 **CPU Usage:** Stable performance")
                    elif cpu_trend > 0:
                        st.warning("📈 **CPU Usage:** Increasing trend detected")
                    else:
                        st.success("📉 **CPU Usage:** Decreasing trend - performance improving")

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading system metrics: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

def show_sensor_data(role_manager, selected_user, selected_device):
    """Show comprehensive sensor data monitoring"""
    if not role_manager.can_access_feature(st.session_state.email, "sensor_data"):
        st.error("🚫 Access Denied: You don't have permission to view sensor data")
        return
    
    st.markdown('<div class="device-monitoring">', unsafe_allow_html=True)
    st.subheader(f"📡 Sensor Data Monitoring - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)
        sensor_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("sensor_data")
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            sensor_type = st.selectbox("📡 Sensor Type", ["All", "Accelerometer", "Gyroscope", "Light", "Proximity", "Heart Rate", "Step Counter"])

        # Get sensor data
        start_time = datetime.combine(selected_date, datetime.min.time())
        end_time = datetime.combine(selected_date, datetime.max.time())
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        sensor_docs = sensor_ref.where("timestamp", ">=", start_timestamp).where("timestamp", "<=", end_timestamp).limit(1000).stream()
        
        sensor_data = []
        for doc in sensor_docs:
            entry = doc.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            sensor_data.append(entry)

        if not sensor_data:
            st.info(f"📡 No sensor data found for {selected_date}.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        df = pd.DataFrame(sensor_data)
        
        # Filter by sensor type
        if sensor_type != "All":
            df = df[df.get("sensorType", "").str.contains(sensor_type, case=False, na=False)]

        if df.empty:
            st.info(f"📡 No {sensor_type.lower()} sensor data found for {selected_date}.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        # Sensor Statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📡 Total Readings", len(df))
        with col2:
            sensor_types = df.get("sensorType", pd.Series()).nunique()
            st.metric("🔢 Sensor Types", sensor_types)
        with col3:
            if not df.empty:
                time_span = df["timestamp"].max() - df["timestamp"].min()
                st.metric("⏱️ Time Span", f"{time_span.total_seconds()/3600:.1f}h")
        with col4:
            reading_rate = len(df) / max(1, (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / 60)
            st.metric("📊 Readings/min", f"{reading_rate:.1f}")

        # Sensor Data Visualization
        st.markdown("### 📈 Sensor Readings")
        
        # Group by sensor type
        sensor_types_available = df.get("sensorType", pd.Series()).dropna().unique()
        
        for sensor in sensor_types_available:
            sensor_df = df[df.get("sensorType") == sensor].sort_values("timestamp")
            
            if len(sensor_df) > 0:
                st.markdown(f"#### 📡 {sensor} Data")
                
                # Create multi-axis plot based on sensor type
                if "accelerometer" in sensor.lower():
                    if all(col in sensor_df.columns for col in ["x", "y", "z"]):
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["x"], name="X-axis", line=dict(color="red")))
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["y"], name="Y-axis", line=dict(color="green")))
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["z"], name="Z-axis", line=dict(color="blue")))
                        fig.update_layout(title=f"{sensor} - 3-Axis Data", xaxis_title="Time", yaxis_title="Acceleration (m/s²)")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif "gyroscope" in sensor.lower():
                    if all(col in sensor_df.columns for col in ["x", "y", "z"]):
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["x"], name="X-axis", line=dict(color="red")))
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["y"], name="Y-axis", line=dict(color="green")))
                        fig.add_trace(go.Scatter(x=sensor_df["timestamp"], y=sensor_df["z"], name="Z-axis", line=dict(color="blue")))
                        fig.update_layout(title=f"{sensor} - Angular Velocity", xaxis_title="Time", yaxis_title="Angular Velocity (rad/s)")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif "light" in sensor.lower():
                    if "value" in sensor_df.columns:
                        fig = px.line(sensor_df, x="timestamp", y="value", title=f"{sensor} - Light Level")
                        fig.update_yaxis(title="Light Level (lux)")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif "proximity" in sensor.lower():
                    if "value" in sensor_df.columns:
                        fig = px.scatter(sensor_df, x="timestamp", y="value", title=f"{sensor} - Proximity Detection")
                        fig.update_yaxis(title="Distance (cm)")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif "heart" in sensor.lower():
                    if "value" in sensor_df.columns:
                        fig = px.line(sensor_df, x="timestamp", y="value", title=f"{sensor} - Heart Rate")
                        fig.update_yaxis(title="BPM")
                        fig.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="Normal Range")
                        fig.add_hline(y=100, line_dash="dash", line_color="orange", annotation_text="Elevated")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif "step" in sensor.lower():
                    if "value" in sensor_df.columns:
                        fig = px.line(sensor_df, x="timestamp", y="value", title=f"{sensor} - Step Count")
                        fig.update_yaxis(title="Steps")
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    # Generic sensor display
                    if "value" in sensor_df.columns:
                        fig = px.line(sensor_df, x="timestamp", y="value", title=f"{sensor} - Sensor Value")
                        st.plotly_chart(fig, use_container_width=True)

        # Activity Analysis
        st.markdown("### 🏃 Activity Analysis")
        
        # Look for accelerometer data to analyze movement patterns
        accel_data = df[df.get("sensorType", "").str.contains("accelerometer", case=False, na=False)]
        
        if not accel_data.empty and all(col in accel_data.columns for col in ["x", "y", "z"]):
            # Calculate magnitude of acceleration
            accel_data = accel_data.copy()
            accel_data["magnitude"] = np.sqrt(accel_data["x"]**2 + accel_data["y"]**2 + accel_data["z"]**2)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Activity level based on acceleration magnitude
                activity_threshold = 12  # m/s²
                active_periods = accel_data[accel_data["magnitude"] > activity_threshold]
                activity_percentage = len(active_periods) / len(accel_data) * 100
                
                if activity_percentage > 30:
                    st.success(f"🏃 High Activity: {activity_percentage:.1f}% active periods")
                elif activity_percentage > 10:
                    st.info(f"🚶 Moderate Activity: {activity_percentage:.1f}% active periods")
                else:
                    st.warning(f"😴 Low Activity: {activity_percentage:.1f}% active periods")
            
            with col2:
                # Movement pattern analysis
                magnitude_std = accel_data["magnitude"].std()
                if magnitude_std > 5:
                    st.info("📊 Variable Movement: High activity variation")
                elif magnitude_std > 2:
                    st.info("📊 Moderate Movement: Some activity variation")
                else:
                    st.info("📊 Stable Movement: Low activity variation")

        # Sensor Health Status
        with st.expander("🔍 Sensor Health Analysis"):
            st.markdown("#### 📡 Sensor Status:")
            
            for sensor in sensor_types_available:
                sensor_df = df[df.get("sensorType") == sensor]
                
                # Check data continuity
                if len(sensor_df) > 1:
                    time_gaps = sensor_df["timestamp"].diff().dt.total_seconds()
                    avg_interval = time_gaps.mean()
                    max_gap = time_gaps.max()
                    
                    if max_gap > avg_interval * 3:
                        st.warning(f"⚠️ **{sensor}:** Irregular data (max gap: {max_gap:.1f}s)")
                    else:
                        st.success(f"✅ **{sensor}:** Consistent data (avg interval: {avg_interval:.1f}s)")
                else:
                    st.info(f"📊 **{sensor}:** Limited data available")

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading sensor data: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

# Update the existing location, call logs, contacts, messages, phone state, and weather functions to include enhanced features
def show_locations(role_manager, selected_user, selected_device):
    """Enhanced location tracking with weather integration"""
    if not role_manager.can_access_feature(st.session_state.email, "locations"):
        st.error("🚫 Access Denied: You don't have permission to view locations")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's location data")
        return
    
    st.subheader(f"🌍 Enhanced Location Tracker - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)

        # Enhanced date and time filters
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            hour_range = st.select_slider(
                "🕐 Select Hour Range", 
                options=list(range(24)), 
                value=(0, 23),
                format_func=lambda x: f"{x:02d}:00"
            )
        with col3:
            accuracy_filter = st.selectbox("🎯 Accuracy Filter", ["All", "High (≤10m)", "Medium (≤50m)", "Low (>50m)"])

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

        # Apply accuracy filter
        if accuracy_filter != "All":
            if accuracy_filter == "High (≤10m)":
                df = df[df.get("accuracy", float('inf')) <= 10]
            elif accuracy_filter == "Medium (≤50m)":
                df = df[df.get("accuracy", float('inf')) <= 50]
            elif accuracy_filter == "Low (>50m)":
                df = df[df.get("accuracy", float('inf')) > 50]

        if df.empty:
            st.info("📍 No location data matches your filters")
            return

        # Enhanced statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📍 Total Locations", len(df))
        with col2:
            st.metric("⏰ First Record", df["timestamp"].min().strftime("%H:%M:%S"))
        with col3:
            st.metric("⏰ Last Record", df["timestamp"].max().strftime("%H:%M:%S"))
        with col4:
            duration = df["timestamp"].max() - df["timestamp"].min()
            st.metric("⌛ Duration", f"{duration.total_seconds()/3600:.1f}h")
        with col5:
            if "accuracy" in df.columns:
                avg_accuracy = df["accuracy"].mean()
                st.metric("🎯 Avg Accuracy", f"{avg_accuracy:.1f}m")

        # Distance and speed analysis
        if len(df) > 1:
            # Calculate distances between consecutive points
            df["prev_lat"] = df["latitude"].shift(1)
            df["prev_lon"] = df["longitude"].shift(1)
            df["prev_time"] = df["timestamp"].shift(1)
            
            # Haversine distance calculation
            def haversine_distance(lat1, lon1, lat2, lon2):
                from math import radians, cos, sin, asin, sqrt
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                return 2 * asin(sqrt(a)) * 6371000  # Earth radius in meters
            
            distances = []
            speeds = []
            for i in range(1, len(df)):
                row = df.iloc[i]
                if pd.notna(row["prev_lat"]):
                    dist = haversine_distance(
                        row["prev_lat"], row["prev_lon"],
                        row["latitude"], row["longitude"]
                    )
                    time_diff = (row["timestamp"] - row["prev_time"]).total_seconds()
                    if time_diff > 0:
                        speed = dist / time_diff * 3.6  # Convert to km/h
                        distances.append(dist)
                        speeds.append(speed)
            
            if distances:
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_distance = sum(distances) / 1000  # Convert to km
                    st.metric("🚶 Total Distance", f"{total_distance:.2f} km")
                with col2:
                    avg_speed = np.mean(speeds) if speeds else 0
                    st.metric("⚡ Avg Speed", f"{avg_speed:.1f} km/h")
                with col3:
                    max_speed = max(speeds) if speeds else 0
                    st.metric("🏎️ Max Speed", f"{max_speed:.1f} km/h")

        # Enhanced map visualization
        st.markdown("### 🗺️ Location Path with Analytics")
        
        if len(df) > 1:
            # Create enhanced map with speed coloring
            fig = go.Figure()
            
            # Add path as lines with speed-based coloring
            if distances:
                # Color points by speed
                speed_colors = speeds if speeds else [0] * len(df)
                
                fig.add_trace(go.Scattermapbox(
                    mode="markers+lines",
                    lon=df['longitude'],
                    lat=df['latitude'],
                    marker={
                        'size': 8, 
                        'color': speed_colors,
                        'colorscale': 'Viridis',
                        'showscale': True,
                        'colorbar': {'title': 'Speed (km/h)'}
                    },
                    line={'width': 3, 'color': 'blue'},
                    text=[f"Time: {ts.strftime('%H:%M:%S')}<br>Speed: {speed:.1f} km/h" 
                          for ts, speed in zip(df['timestamp'], [0] + speeds)],
                    name="Location Path",
                    hovertemplate="<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>"
                ))
            else:
                fig.add_trace(go.Scattermapbox(
                    mode="markers+lines",
                    lon=df['longitude'],
                    lat=df['latitude'],
                    marker={'size': 8, 'color': 'red'},
                    line={'width': 3, 'color': 'blue'},
                    text=df['timestamp'].dt.strftime('%H:%M:%S'),
                    name="Location Path"
                ))
            
            # Add start and end points
            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=[df.iloc[0]['longitude']],
                lat=[df.iloc[0]['latitude']],
                marker={'size': 15, 'color': 'green'},
                text="Start",
                name="Start Point"
            ))
            
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

        # Location analytics
        with st.expander("📊 Location Analytics"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Time-based analysis
                df['hour'] = df['timestamp'].dt.hour
                hourly_counts = df.groupby('hour').size()
                
                fig_hourly = px.bar(
                    x=hourly_counts.index,
                    y=hourly_counts.values,
                    title="Location Updates by Hour",
                    labels={'x': 'Hour of Day', 'y': 'Number of Updates'}
                )
                st.plotly_chart(fig_hourly, use_container_width=True)
            
            with col2:
                # Accuracy distribution
                if "accuracy" in df.columns:
                    fig_accuracy = px.histogram(
                        df,
                        x="accuracy",
                        nbins=20,
                        title="Location Accuracy Distribution",
                        labels={'x': 'Accuracy (meters)', 'y': 'Count'}
                    )
                    st.plotly_chart(fig_accuracy, use_container_width=True)

        # Recent locations table with enhanced info
        with st.expander("📋 Detailed Location Records"):
            display_df = df[["timestamp", "latitude", "longitude"]].copy()
            if "accuracy" in df.columns:
                display_df["accuracy"] = df["accuracy"]
            if "provider" in df.columns:
                display_df["provider"] = df["provider"]
            if "altitude" in df.columns:
                display_df["altitude"] = df["altitude"]
            
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading location data: {str(e)}")

# Enhanced main function with comprehensive features
def main():
    """Main application logic with enhanced Firebase role-based access control"""
    
    # Initialize session state for admin dashboard
    if "show_admin_dashboard" not in st.session_state:
        st.session_state.show_admin_dashboard = False
    
    # App header with enhanced styling
    st.markdown('''
    <div class="main-header">
        <h1>🛡️ Guardian Dashboard v3.0</h1>
        <p>Comprehensive Device Monitoring, Analytics & Security Platform</p>
        <small>Supporting Android 14+ with Offline Transcription & Real-time Analytics</small>
    </div>
    ''', unsafe_allow_html=True)

    # Authentication check
    if not login():
        st.info("👆 Please log in to access the comprehensive monitoring dashboard")
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
    user_agent = "Streamlit Guardian Dashboard v3.0"
    
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

    # Enhanced user role information in sidebar
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

    # Enhanced sidebar navigation with comprehensive features
    st.sidebar.markdown("---")
    st.sidebar.title("📊 Navigation")
    
    # Build available pages based on permissions with enhanced features
    all_pages = {
        "📱 Device Overview": ("device_overview", show_device_overview),
        "🌍 Location Tracker": ("locations", show_locations),
        "🌦️ Weather Dashboard": ("weather", show_weather),
        "📞 Call Logs": ("call_logs", show_call_logs),
        "👥 Contacts": ("contacts", show_contacts),
        "💬 Messages": ("messages", show_messages),
        "📶 Phone State": ("phone_state", show_phone_state),
        "🎙️ Audio Recordings": ("audio_recordings", show_audio_recordings),
        "📱 Installed Apps": ("installed_apps", show_installed_apps),
        "📊 App Usage Analytics": ("app_usage", show_app_usage),
        "🔋 Battery Monitoring": ("battery_status", show_battery_status),
        "🖥️ System Metrics": ("system_metrics", show_system_metrics),
        "📡 Sensor Data": ("sensor_data", show_sensor_data)
    }
    
    available_pages = {}
    for page_name, (permission, function) in all_pages.items():
        if role_manager.can_access_feature(current_user_email, permission):
            available_pages[page_name] = function
    
    if not available_pages:
        st.error("🚫 No features available for your account. Please contact administrator.")
        return
    
    # Enhanced page selection with categories
    st.sidebar.markdown("#### 📱 Device & Location")
    device_pages = ["📱 Device Overview", "🌍 Location Tracker", "🌦️ Weather Dashboard"]
    
    st.sidebar.markdown("#### 📞 Communication")
    comm_pages = ["📞 Call Logs", "👥 Contacts", "💬 Messages", "📶 Phone State"]
    
    st.sidebar.markdown("#### 🎙️ Audio & Media")
    audio_pages = ["🎙️ Audio Recordings"]
    
    st.sidebar.markdown("#### 📊 System Monitoring")
    system_pages = ["📱 Installed Apps", "📊 App Usage Analytics", "🔋 Battery Monitoring", "🖥️ System Metrics", "📡 Sensor Data"]
    
    # Create a single selectbox with all available pages
    available_page_names = list(available_pages.keys())
    selected_page = st.sidebar.selectbox(
        "Choose a section:",
        available_page_names,
        index=0
    )
    
    # Show feature availability status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Feature Status")
    
    feature_status = {
        "📱 Core Monitoring": "✅ Active",
        "🎙️ Audio Transcription": "✅ Offline Support",
        "🌦️ Weather Integration": "✅ Real-time",
        "📊 Analytics Engine": "✅ Enhanced",
        "🔐 Security": "✅ Role-based"
    }
    
    for feature, status in feature_status.items():
        st.sidebar.write(f"{feature}: {status}")
    
    # User info and system status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(f"🔐 Logged in as:\n{current_user_email}")
    
    # Show current device info
    if selected_user and selected_device:
        st.sidebar.markdown("### 📱 Current Selection")
        st.sidebar.write(f"👤 **User:** {selected_user}")
        st.sidebar.write(f"📱 **Device:** {selected_device[:12]}...")
        
        # Quick device status check
        try:
            user_email_sanitized = role_manager.sanitize_email(selected_user)
            device_ref = role_manager.db.collection("users").document(user_email_sanitized).collection("devices").document(selected_device)
            device_doc = device_ref.get()
            
            if device_doc.exists:
                device_data = device_doc.to_dict()
                is_active = device_data.get('isActive', False)
                if is_active:
                    st.sidebar.success("🟢 Device Active")
                else:
                    st.sidebar.error("🔴 Device Inactive")
                
                last_sync = device_data.get('lastSyncTime', 'Never')
                if last_sync != 'Never':
                    try:
                        last_sync_dt = datetime.fromtimestamp(last_sync / 1000.0)
                        time_diff = datetime.now() - last_sync_dt
                        if time_diff.total_seconds() < 3600:
                            st.sidebar.success(f"🔄 Synced: {last_sync_dt.strftime('%H:%M')}")
                        else:
                            st.sidebar.warning(f"⚠️ Last Sync: {last_sync_dt.strftime('%m/%d %H:%M')}")
                    except:
                        st.sidebar.info(f"🔄 Last Sync: {last_sync}")
        except:
            st.sidebar.warning("⚠️ Cannot check device status")
    
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

    # Display selected page with enhanced error handling
    try:
        # Log feature access
        feature_name = [k for k, v in all_pages.items() if v[1] == available_pages[selected_page]][0]
        permission_name = [v[0] for k, v in all_pages.items() if k == feature_name][0]
        role_manager.log_audit_event("feature_accessed", current_user_email, {
            "feature": permission_name,
            "target_user": selected_user,
            "device": selected_device,
            "timestamp": datetime.now().isoformat()
        })
        
        # Show loading indicator for data-intensive pages
        if selected_page in ["📊 App Usage Analytics", "🖥️ System Metrics", "📡 Sensor Data"]:
            with st.spinner(f"Loading {selected_page} data..."):
                available_pages[selected_page](role_manager, selected_user, selected_device)
        else:
            # Call the selected page function
            available_pages[selected_page](role_manager, selected_user, selected_device)
        
    except Exception as e:
        st.error(f"❌ Error loading {selected_page}: {str(e)}")
        st.info("This might be due to missing data or network issues. Please try refreshing the page.")
        
        # Show detailed error for admins
        if role_manager.is_super_admin(current_user_email):
            with st.expander("🔧 Technical Details (Admin Only)"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())

    # Footer with system information
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>🛡️ Guardian Dashboard v3.0<br>
            Enhanced Monitoring & Analytics</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='text-align: center; color: #666;'>
            <small>📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}<br>
            🌍 {location_info.get('location', 'Unknown Location')}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <small>🔐 Role-based Security<br>
            ☁️ Firebase Backend</small>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()