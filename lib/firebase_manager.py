# lib/firebase_manager.py
"""
Firebase management and initialization
"""

import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
from .config import GuardianConfig

class FirebaseManager:
    """Manage Firebase initialization and connection"""
    
    def __init__(self, config: GuardianConfig):
        self.config = config
        self._db = None
    
    @st.cache_resource
    def init_firebase(_self):
        """Initialize Firebase Admin SDK with environment variables"""
        try:
            # Validate configuration
            _self.config.validate_firebase_config()
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(_self.config.firebase_config)
            initialize_app(cred)
            
            _self._db = firestore.client()
            return _self._db
            
        except Exception as e:
            st.error(f"❌ Firebase initialization failed: {str(e)}")
            st.info("Check your Firebase credentials in .env file")
            st.stop()
    
    @property
    def db(self):
        """Get Firestore database instance"""
        if self._db is None:
            self._db = self.init_firebase()
        return self._db