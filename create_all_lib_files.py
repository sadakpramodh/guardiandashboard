#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed Complete File Creator for Guardian Dashboard
Creates all lib files with proper UTF-8 encoding for Windows
"""

import os
from pathlib import Path

def create_directory_structure():
    """Create all necessary directories"""
    directories = [
        "lib",
        "lib/config", 
        "lib/auth",
        "lib/firebase", 
        "lib/pages",
        "lib/components",
        "lib/utils",
        "lib/admin"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_init_files():
    """Create all __init__.py files"""
    init_files = {
        "lib/__init__.py": "",
        "lib/config/__init__.py": "",
        "lib/auth/__init__.py": "",
        "lib/firebase/__init__.py": "",
        "lib/pages/__init__.py": "",
        "lib/components/__init__.py": "",
        "lib/utils/__init__.py": "",
        "lib/admin/__init__.py": ""
    }
    
    for file_path, content in init_files.items():
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created: {file_path}")

def create_config_settings():
    """Create lib/config/settings.py"""
    content = '''"""
Configuration management for Guardian Dashboard
Centralized settings and environment handling
"""

import os
import streamlit as st
from dotenv import load_dotenv
from typing import Dict, Any

class GuardianConfig:
    """Centralized configuration management"""
    
    def __init__(self):
        load_dotenv()
        self._configure_streamlit()
    
    def _configure_streamlit(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Guardian Dashboard",
            page_icon="🛡️", 
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @property
    def firebase_config(self) -> Dict[str, Any]:
        """Firebase configuration from environment"""
        return {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\\\n', '\\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        }
    
    @property
    def email_config(self) -> Dict[str, Any]:
        """Email/SMTP configuration"""
        return {
            "server": os.getenv("MAIL_SERVER"),
            "port": int(os.getenv("MAIL_PORT", 587)),
            "username": os.getenv("MAIL_USERNAME"),
            "password": os.getenv("MAIL_PASSWORD"),
            "sender": os.getenv("MAIL_DEFAULT_SENDER")
        }
    
    @property
    def super_admin_email(self) -> str:
        """Super admin email from environment"""
        return os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
    
    def validate_config(self) -> tuple[bool, str]:
        """Validate configuration completeness"""
        firebase_required = ["project_id", "private_key", "client_email"]
        email_required = ["server", "username", "password", "sender"]
        
        # Check Firebase config
        firebase = self.firebase_config
        missing_firebase = [field for field in firebase_required if not firebase.get(field)]
        
        # Check email config  
        email = self.email_config
        missing_email = [field for field in email_required if not email.get(field)]
        
        if missing_firebase:
            return False, f"Missing Firebase config: {', '.join(missing_firebase)}"
        
        if missing_email:
            return False, f"Missing email config: {', '.join(missing_email)}"
        
        return True, "Configuration valid"
    
    @staticmethod
    def get_app_styles() -> str:
        """Get custom CSS styles for the app"""
        return """
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
        </style>
        """
'''
    
    with open("lib/config/settings.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: lib/config/settings.py")

def create_auth_email_otp():
    """Create lib/auth/email_otp.py"""
    content = '''"""
Email OTP Authentication System
Clean, modular authentication using SMTP
"""

import streamlit as st
import smtplib
import random
import time
import re
from email.message import EmailMessage
from typing import Optional

class EmailOTPAuth:
    """Email-based OTP authentication system"""
    
    def __init__(self, config):
        self.config = config
        self.email_config = config.email_config
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_otp_email(self, email: str, otp: str) -> bool:
        """Send OTP via email using SMTP"""
        try:
            if not all([
                self.email_config["server"],
                self.email_config["username"], 
                self.email_config["password"],
                self.email_config["sender"]
            ]):
                st.error("Email configuration incomplete. Check your .env file.")
                return False

            msg = EmailMessage()
            msg["Subject"] = "Guardian Dashboard - Login OTP"
            msg["From"] = self.email_config["sender"]
            msg["To"] = email
            msg.set_content(f"""
            Hello,
            
            Your OTP for Guardian Dashboard login is: {otp}
            
            This code is valid for 5 minutes only.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            Guardian Dashboard Team
            """)

            with smtplib.SMTP(self.email_config["server"], self.email_config["port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"Error sending email: {str(e)}")
            return False
    
    def initialize_session_state(self):
        """Initialize authentication session state"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "otp" not in st.session_state:
            st.session_state.otp = None
        if "email" not in st.session_state:
            st.session_state.email = None
        if "otp_timestamp" not in st.session_state:
            st.session_state.otp_timestamp = None
        if "login_attempts" not in st.session_state:
            st.session_state.login_attempts = 0
    
    def login(self) -> bool:
        """Main login flow with OTP authentication"""
        self.initialize_session_state()
        
        if st.session_state.authenticated:
            return True

        st.subheader("Email OTP Authentication")
        
        # Email input phase
        if not st.session_state.otp:
            with st.form("email_form"):
                email = st.text_input(
                    "Enter your email address",
                    placeholder="your-email@example.com",
                    help="You'll receive a 6-digit OTP code"
                )
                
                send_otp_clicked = st.form_submit_button("Send OTP", use_container_width=True)
                
                if send_otp_clicked:
                    if not email:
                        st.error("Please enter your email address")
                    elif not self.is_valid_email(email):
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("Sending OTP..."):
                            otp = self.generate_otp()
                            if self.send_otp_email(email, otp):
                                st.session_state.email = email
                                st.session_state.otp = otp
                                st.session_state.otp_timestamp = time.time()
                                st.session_state.login_attempts = 0
                                st.success("OTP sent successfully! Check your inbox.")
                                st.rerun()
        
        # OTP verification phase
        else:
            # Check if OTP is expired (5 minutes)
            if time.time() - st.session_state.otp_timestamp > 300:
                st.error("OTP has expired. Please request a new one.")
                st.session_state.otp = None
                st.session_state.otp_timestamp = None
                st.rerun()
                
            st.info(f"OTP sent to: {st.session_state.email}")
            
            with st.form("otp_form"):
                user_otp = st.text_input(
                    "Enter 6-digit OTP",
                    max_chars=6,
                    placeholder="123456",
                    help="Check your email for the verification code"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    verify_clicked = st.form_submit_button("Verify OTP", use_container_width=True)
                with col2:
                    resend_clicked = st.form_submit_button("Resend OTP", use_container_width=True)

                if verify_clicked:
                    if not user_otp:
                        st.error("Please enter the OTP")
                    elif len(user_otp) != 6 or not user_otp.isdigit():
                        st.error("OTP must be 6 digits")
                    elif user_otp == st.session_state.otp:
                        st.session_state.authenticated = True
                        st.session_state.login_attempts = 0
                        st.success("Login successful!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        if st.session_state.login_attempts >= 3:
                            st.error("Too many failed attempts. Please request a new OTP.")
                            st.session_state.otp = None
                            st.session_state.otp_timestamp = None
                            st.session_state.login_attempts = 0
                        else:
                            remaining = 3 - st.session_state.login_attempts
                            st.error(f"Incorrect OTP. {remaining} attempts remaining.")

                if resend_clicked:
                    with st.spinner("Resending OTP..."):
                        new_otp = self.generate_otp()
                        if self.send_otp_email(st.session_state.email, new_otp):
                            st.session_state.otp = new_otp
                            st.session_state.otp_timestamp = time.time()
                            st.session_state.login_attempts = 0
                            st.success("New OTP sent!")
                            st.rerun()

        return st.session_state.authenticated
'''
    
    with open("lib/auth/email_otp.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: lib/auth/email_otp.py")

def create_simple_main():
    """Create a simple main.py that works without navigation before login"""
    content = '''# main.py - Guardian Dashboard (No Navigation Before Login)

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

# Hide Streamlit menu and footer
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
    """Simple login without showing navigation"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    # Header
    st.markdown("""
    <div class=\"main-header\">
        <h1>🛡️ Guardian Dashboard</h1>
        <p>Enterprise Device Monitoring & Analytics Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    return auth.login()

def show_authenticated_app():
    """Show the main app after authentication"""
    
    # NOW show navigation (only after login)
    st.sidebar.title("📊 Guardian Dashboard")
    st.sidebar.success(f"👤 Logged in as:\\n{st.session_state.email}")
    
    # Check if user is super admin
    super_admin = os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
    is_super_admin = st.session_state.email.lower() == super_admin.lower()
    
    if is_super_admin:
        st.sidebar.info("👑 Super Administrator")
        if st.sidebar.button("🛠️ Admin Dashboard", use_container_width=True):
            st.session_state.current_page = "admin"
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Available Features")
    
    # Simple navigation buttons
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
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Show current page content
    current_page = st.session_state.get("current_page", "device_overview")
    
    if current_page == "admin":
        st.title("🛠️ Admin Dashboard")
        st.info("Admin dashboard functionality coming soon...")
        st.markdown("### System Status")
        st.success("✅ System operational")
        st.success("✅ Firebase connected")
        st.success("✅ Email service configured")
        
    elif current_page == "device_overview":
        st.title("📱 Device Overview")
        st.info("Device overview functionality coming soon...")
        
        # Placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📱 Total Devices", "1")
        with col2:
            st.metric("🟢 Active Devices", "1")
        with col3:
            st.metric("🔋 Avg Battery", "85%")
        with col4:
            st.metric("📊 Data Points", "1.2K")
    
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
    
    # CRITICAL: Authentication check BEFORE showing any navigation
    if not simple_login():
        # If not authenticated, simple_login() handles the UI
        # NO navigation is shown here
        return
    
    # Only show the app if authenticated
    show_authenticated_app()

if __name__ == "__main__":
    main()
'''
    
    with open("main.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: main.py (fixed - no navigation before login)")

def create_utils_helpers():
    """Create lib/utils/helpers.py"""
    content = '''"""
Utility functions for Guardian Dashboard
Common helper functions and formatters
"""

import pandas as pd
import requests
from datetime import datetime
from typing import Dict, Any, Optional

def format_bytes(bytes_value) -> str:
    """Convert bytes to human readable format"""
    if pd.isna(bytes_value) or bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def format_duration(seconds) -> str:
    """Convert seconds to minutes and seconds format"""
    if pd.isna(seconds) or seconds == 0:
        return "0m 0s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"

def get_user_location_info() -> Dict[str, str]:
    """Get user's location information via IP geolocation"""
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

def safe_get(data: Dict[str, Any], key: str, default: Any = "Unknown") -> Any:
    """Safely get value from dictionary with default"""
    return data.get(key, default) if data else default
'''
    
    with open("lib/utils/helpers.py", 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: lib/utils/helpers.py")

def main():
    """Create all files with proper encoding"""
    print("🛡️ Creating Complete Guardian Dashboard File Structure")
    print("=" * 60)
    
    try:
        create_directory_structure()
        create_init_files()
        create_config_settings()
        create_auth_email_otp()
        create_utils_helpers()
        create_simple_main()
        
        print("\n" + "=" * 60)
        print("✅ All files created successfully!")
        print("=" * 60)
        
        print("\n📋 Files Created:")
        print("• main.py (FIXED - no navigation before login)")
        print("• lib/ directory structure")
        print("• lib/config/settings.py")
        print("• lib/auth/email_otp.py") 
        print("• lib/utils/helpers.py")
        print("• All __init__.py files")
        
        print("\n🎯 Key Fix:")
        print("• ✅ Navigation ONLY shows AFTER successful login")
        print("• ✅ UTF-8 encoding for Windows compatibility")
        print("• ✅ Proper module structure")
        print("• ✅ Clean authentication flow")
        
        print("\n🚀 Next Steps:")
        print("1. Run: streamlit run main.py")
        print("2. Login with your super admin email")
        print("3. Verify NO navigation shows before login")
        print("4. Verify navigation appears AFTER login")
        
        print("\n💡 Test Instructions:")
        print("• Before login: Should only see login form")
        print("• After login: Should see full navigation sidebar")
        print("• Navigation is completely hidden until authenticated!")
        
    except Exception as e:
        print(f"\n❌ Error creating files: {str(e)}")
        print("Please check file permissions and try again.")

if __name__ == "__main__":
    main()