# lib/components.py
"""
Reusable UI components for Guardian Dashboard
"""

import streamlit as st
from datetime import datetime

class GuardianComponents:
    """Collection of reusable UI components"""
    
    @staticmethod
    def render_header():
        """Render the main dashboard header"""
        st.markdown('''
        <div class="main-header">
            <h1>🛡️ Guardian Dashboard v3.0</h1>
            <p>Comprehensive Device Monitoring, Analytics & Security Platform</p>
            <small>Supporting Android 14+ with Offline Transcription & Real-time Analytics</small>
        </div>
        ''', unsafe_allow_html=True)
    
    @staticmethod
    def render_user_device_selector(role_manager, current_user_email):
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
    
    @staticmethod
    def render_sidebar_navigation(role_manager, current_user_email, all_pages):
        """Render enhanced sidebar navigation"""
        
        # Enhanced user role information
        st.sidebar.markdown("### 🔐 Access Information")
        if role_manager.is_super_admin(current_user_email):
            st.sidebar.success("👑 Super Administrator")
            st.sidebar.info("✅ Full system access")
            
            # Add admin dashboard option
            if st.sidebar.button("🛠️ Admin Dashboard"):
                st.session_state.show_admin_dashboard = True
                st.rerun()
        else:
            user_profile = role_manager.get_user_profile(current_user_email)
            st.sidebar.info(f"👤 User\n📧 {current_user_email}")
            permissions = user_profile.get("permissions", {})
            st.sidebar.write("**Your Permissions:**")
            for perm, granted in permissions.items():
                if granted:
                    st.sidebar.write(f"✅ {perm.replace('_', ' ').title()}")
        
        # Build available pages based on permissions
        available_pages = {}
        for page_name, (permission, function) in all_pages.items():
            if role_manager.can_access_feature(current_user_email, permission):
                available_pages[page_name] = function
        
        if not available_pages:
            st.error("🚫 No features available for your account. Please contact administrator.")
            return None, None
        
        # Enhanced sidebar navigation
        st.sidebar.markdown("---")
        st.sidebar.title("📊 Navigation")
        
        # Enhanced page selection with categories
        st.sidebar.markdown("#### 📱 Device & Location")
        st.sidebar.markdown("#### 📞 Communication")
        st.sidebar.markdown("#### 🎙️ Audio & Media")
        st.sidebar.markdown("#### 📊 System Monitoring")
        
        # Create a single selectbox with all available pages
        available_page_names = list(available_pages.keys())
        selected_page = st.sidebar.selectbox(
            "Choose a section:",
            available_page_names,
            index=0
        )
        
        return available_pages, selected_page
    
    @staticmethod
    def render_sidebar_status():
        """Render feature status in sidebar"""
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
    
    @staticmethod
    def render_device_status(role_manager, selected_user, selected_device):
        """Render current device status in sidebar"""
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
    
    @staticmethod
    def render_footer(location_info):
        """Render dashboard footer"""
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