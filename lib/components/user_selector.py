"""
User and Device Selector Component
Handles user/device selection with proper permission checking
"""

import streamlit as st
from typing import Tuple, Optional
from lib.utils.helpers import safe_get

class UserDeviceSelector:
    """User and device selector component"""
    
    def __init__(self, role_manager):
        self.role_manager = role_manager
    
    def render(self, current_user_email: str) -> Tuple[Optional[str], Optional[str]]:
        """Render user and device selector"""
        # Get accessible users for current user
        accessible_users = self.role_manager.get_accessible_users(current_user_email)
        
        if not accessible_users:
            st.sidebar.warning("No accessible users found")
            return None, None
        
        st.sidebar.markdown("### 👥 User & Device Selection")
        
        # User selection
        selected_user = self._render_user_selector(accessible_users)
        
        if not selected_user:
            return None, None
        
        # Device selection
        selected_device = self._render_device_selector(selected_user)
        
        return selected_user, selected_device
    
    def _render_user_selector(self, accessible_users: list) -> Optional[str]:
        """Render user selection interface"""
        user_emails = [user["email"] for user in accessible_users]
        
        if len(user_emails) == 1:
            selected_user = user_emails[0]
            st.sidebar.info(f"👤 Viewing: {selected_user}")
            return selected_user
        else:
            selected_user = st.sidebar.selectbox(
                "👤 Select User",
                user_emails,
                key="user_selector"
            )
            return selected_user
    
    def _render_device_selector(self, selected_user: str) -> Optional[str]:
        """Render device selection interface"""
        # Get devices for selected user
        user_email_sanitized = self.role_manager.sanitize_email(selected_user)
        
        try:
            devices_ref = self.role_manager.db.collection("users").document(user_email_sanitized).collection("devices")
            devices = devices_ref.stream()
            device_map = {doc.id: doc.to_dict() for doc in devices}
            
            if not device_map:
                st.sidebar.warning(f"No devices found for {selected_user}")
                return None
            
            device_ids = list(device_map.keys())
            
            if len(device_ids) == 1:
                selected_device = device_ids[0]
                device_info = device_map[selected_device]
                device_name = safe_get(device_info, 'device')
                brand = safe_get(device_info, 'brand')
                st.sidebar.info(f"📱 Device: {device_name} ({brand})")
                return selected_device
            else:
                # Show device info in selection
                device_options = []
                for device_id in device_ids:
                    device_info = device_map[device_id]
                    device_name = safe_get(device_info, 'device')
                    brand = safe_get(device_info, 'brand')
                    device_options.append(f"{device_name} ({brand}) - {device_id[:8]}...")
                
                selected_idx = st.sidebar.selectbox(
                    "📱 Select Device",
                    range(len(device_options)),
                    format_func=lambda x: device_options[x],
                    key="device_selector"
                )
                return device_ids[selected_idx]
            
        except Exception as e:
            st.sidebar.error(f"Error fetching devices: {str(e)}")
            return None
    
    def render_device_status(self, selected_user: str, selected_device: str):
        """Render current device status in sidebar"""
        if not (selected_user and selected_device):
            return
        
        st.sidebar.markdown("### 📱 Current Selection")
        st.sidebar.write(f"👤 **User:** {selected_user}")
        st.sidebar.write(f"📱 **Device:** {selected_device[:12]}...")
        
        # Quick device status check
        try:
            user_email_sanitized = self.role_manager.sanitize_email(selected_user)
            device_ref = self.role_manager.db.collection("users").document(user_email_sanitized).collection("devices").document(selected_device)
            device_doc = device_ref.get()
            
            if device_doc.exists:
                device_data = device_doc.to_dict()
                is_active = device_data.get('isActive', False)
                
                if is_active:
                    st.sidebar.success("🟢 Device Active")
                else:
                    st.sidebar.error("🔴 Device Inactive")
                
                # Show last sync time
                last_sync = device_data.get('lastUpdated', device_data.get('lastSyncTime'))
                if last_sync and last_sync != 'Never':
                    try:
                        from datetime import datetime
                        last_sync_dt = datetime.fromtimestamp(last_sync / 1000.0)
                        time_diff = datetime.now() - last_sync_dt
                        if time_diff.total_seconds() < 3600:
                            st.sidebar.success(f"🔄 Synced: {last_sync_dt.strftime('%H:%M')}")
                        else:
                            st.sidebar.warning(f"⚠️ Last Sync: {last_sync_dt.strftime('%m/%d %H:%M')}")
                    except:
                        st.sidebar.info("🔄 Sync status unknown")
                else:
                    st.sidebar.error("❌ Never synced")
        except:
            st.sidebar.warning("⚠️ Cannot check device status")