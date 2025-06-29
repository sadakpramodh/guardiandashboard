# main.py – Clean Guardian Dashboard Main File

import streamlit as st
from datetime import datetime

# Import Guardian Dashboard Library
from lib import GuardianConfig, FirebaseManager
from lib.components import GuardianComponents
from lib.utils import get_user_location_info
from lib.pages import ALL_PAGES

# Import existing modules
from auth import login
from firebase_role_manager import FirebaseRoleManager
from admin_management import show_admin_dashboard

def main():
    """Main application logic with enhanced Firebase role-based access control"""
    
    # Initialize Guardian Dashboard
    config = GuardianConfig()
    firebase_manager = FirebaseManager(config)
    components = GuardianComponents()
    
    # Initialize session state for admin dashboard
    if "show_admin_dashboard" not in st.session_state:
        st.session_state.show_admin_dashboard = False
    
    # Render header
    components.render_header()

    # Authentication check
    if not login():
        st.info("👆 Please log in to access the comprehensive monitoring dashboard")
        return

    # Initialize Firebase and Role Manager
    db = firebase_manager.db
    role_manager = FirebaseRoleManager(db)
    
    current_user_email = st.session_state.email
    
    # Initialize system if this is the first super admin login
    if current_user_email.lower() == config.super_admin_email.lower():
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

    # Render sidebar navigation
    available_pages, selected_page = components.render_sidebar_navigation(
        role_manager, current_user_email, ALL_PAGES
    )
    
    if not available_pages:
        return

    # Check if admin dashboard should be shown
    if st.session_state.get("show_admin_dashboard", False):
        show_admin_dashboard(db, current_user_email)
        
        if st.sidebar.button("📊 Back to Main Dashboard"):
            st.session_state.show_admin_dashboard = False
            st.rerun()
        return

    # User and device selection
    selected_user, selected_device = components.render_user_device_selector(
        role_manager, current_user_email
    )
    
    if not selected_user or not selected_device:
        st.warning("⚠️ Please select a user and device to continue")
        return

    # Render feature status and device status
    components.render_sidebar_status()
    components.render_device_status(role_manager, selected_user, selected_device)
    
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

    # Display selected page with enhanced error handling
    try:
        # Log feature access
        feature_name = [k for k, v in ALL_PAGES.items() if v[1] == available_pages[selected_page]][0]
        permission_name = [v[0] for k, v in ALL_PAGES.items() if k == feature_name][0]
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

    # Render footer
    components.render_footer(location_info)

if __name__ == "__main__":
    main()