# lib/config.py
"""
Configuration management for Guardian Dashboard
"""

import streamlit as st
import os
from dotenv import load_dotenv

class GuardianConfig:
    """Central configuration management"""
    
    def __init__(self):
        load_dotenv()
        self.setup_streamlit_config()
        self.setup_styling()
    
    def setup_streamlit_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Guardian Dashboard",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_styling(self):
        """Apply custom CSS styling"""
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
    
    @property
    def firebase_config(self):
        """Get Firebase configuration from environment variables"""
        return {
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
    
    @property
    def super_admin_email(self):
        """Get super admin email"""
        return os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
    
    def validate_firebase_config(self):
        """Validate Firebase configuration"""
        required_fields = ["project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if not self.firebase_config.get(field)]
        
        if missing_fields:
            st.error(f"⚠️ Missing Firebase configuration: {', '.join(missing_fields)}")
            st.info("Please check your .env file for missing Firebase credentials")
            st.stop()
        
        return True