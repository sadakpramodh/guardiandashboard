# main.py - Guardian Dashboard (Fixed - No Navigation Before Login)

import streamlit as st
import os
from dotenv import load_dotenv
import auth

# Load environment first
load_dotenv()

# Configure Streamlit
st.set_page_config(
    page_title="Guardian Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Hide Streamlit menu
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {visibility: hidden;}
div[data-testid="stDecoration"] {visibility: hidden;}
div[data-testid="stStatusWidget"] {visibility: hidden;}

.main-header {
    text-align: center;
    padding: 1.5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

def simple_login():
    """OTP-based login with custom header"""
    st.markdown('''
    <div class="main-header">
        <h1>🛡️ Guardian Dashboard</h1>
        <p>Enterprise Device Monitoring & Analytics Platform</p>
    </div>
    ''', unsafe_allow_html=True)
    return auth.login()

def show_authenticated_app():
    """Show the main app ONLY after authentication"""
    
    # Navigation appears HERE (only after login)
    st.sidebar.title("📊 Guardian Dashboard")
    st.sidebar.success(f"👤 Logged in as:\n{st.session_state.email}")
    
    # Check if user is super admin
    super_admin = os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
    is_super_admin = st.session_state.email.lower() == super_admin.lower()
    
    if is_super_admin:
        st.sidebar.info("👑 Super Administrator")
        if st.sidebar.button("🛠️ Admin Dashboard", use_container_width=True):
            st.session_state.current_page = "admin"
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Available Features")
    
    # Navigation buttons (only shown after login)
    if st.sidebar.button("📱 Device Overview", use_container_width=True):
        st.session_state.current_page = "device_overview"
    
    if st.sidebar.button("🌍 Location Tracker", use_container_width=True):
        st.session_state.current_page = "locations"
    
    if st.sidebar.button("🌦️ Weather Dashboard", use_container_width=True):
        st.session_state.current_page = "weather"
    
    if st.sidebar.button("📞 Call Logs", use_container_width=True):
        st.session_state.current_page = "call_logs"
    
    if st.sidebar.button("💬 Messages", use_container_width=True):
        st.session_state.current_page = "messages"
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Show current page content
    current_page = st.session_state.get("current_page", "device_overview")
    
    if current_page == "admin":
        st.title("🛠️ Admin Dashboard")
        st.success("✅ System operational")
        st.info("Admin dashboard functionality coming soon...")
        
    elif current_page == "device_overview":
        st.title("📱 Device Overview")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📱 Total Devices", "1")
        with col2:
            st.metric("🟢 Active Devices", "1") 
        with col3:
            st.metric("🔋 Avg Battery", "85%")
        with col4:
            st.metric("📊 Data Points", "1.2K")
        st.info("Full device overview functionality coming soon...")
    
    elif current_page == "locations":
        st.title("🌍 Location Tracker")
        st.info("Location tracking functionality coming soon...")
        
    elif current_page == "weather":
        st.title("🌦️ Weather Dashboard") 
        st.info("Weather dashboard functionality coming soon...")
        
    elif current_page == "call_logs":
        st.title("📞 Call Logs")
        st.info("Call logs functionality coming soon...")
        
    elif current_page == "messages":
        st.title("💬 Messages")
        st.info("Messages functionality coming soon...")

def main():
    """Main application entry point"""
    
    # CRITICAL: Authentication check FIRST
    if not simple_login():
        # If not authenticated, ONLY show login form
        # NO navigation, NO sidebar, NO features
        return
    
    # ONLY show the full app if authenticated
    show_authenticated_app()

if __name__ == "__main__":
    main()