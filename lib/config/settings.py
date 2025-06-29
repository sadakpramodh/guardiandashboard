"""
Configuration management for Guardian Dashboard
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
        </style>
        """