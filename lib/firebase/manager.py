"""
Firebase Integration Manager
Handles Firebase initialization and basic operations
"""

import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
from typing import Optional
from lib.config.settings import GuardianConfig

class FirebaseManager:
    """Firebase integration and management"""
    
    def __init__(self, config: GuardianConfig):
        self.config = config
        self._db = None
    
    @st.cache_resource
    def initialize_firebase(_self) -> Optional[firestore.Client]:
        """Initialize Firebase Admin SDK with caching"""
        try:
            # Check if already initialized
            try:
                firebase_admin.get_app()
                return firestore.client()
            except ValueError:
                pass
            
            firebase_config = _self.config.firebase_config
            
            # Validate required fields
            required_fields = ["project_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if not firebase_config.get(field)]
            
            if missing_fields:
                st.error(f"⚠️ Missing Firebase configuration: {', '.join(missing_fields)}")
                st.info("Please check your .env file for missing Firebase credentials")
                st.stop()

            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(firebase_config)
            initialize_app(cred)
            
            return firestore.client()
            
        except Exception as e:
            st.error(f"❌ Firebase initialization failed: {str(e)}")
            st.info("Check your Firebase credentials in .env file")
            st.stop()
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore database client"""
        if self._db is None:
            self._db = self.initialize_firebase()
        return self._db
    
    def test_connection(self) -> bool:
        """Test Firebase connection"""
        try:
            # Try to access a test collection
            test_ref = self.db.collection("connection_test")
            test_ref.limit(1).get()
            return True
        except Exception as e:
            st.error(f"Firebase connection test failed: {str(e)}")
            return False
    
    def get_collection_count(self, collection_path: str) -> int:
        """Get document count for a collection"""
        try:
            docs = list(self.db.collection(collection_path).limit(1).stream())
            return len(docs)
        except:
            return 0
    
    def sanitize_email(self, email: str) -> str:
        """Convert email to Firebase-safe document ID"""
        return email.replace('.', '_dot_').replace('@', '_at_') \
            .replace('/', '_').replace('[', '_').replace(']', '_') \
            .replace('*', '_').replace('?', '_')
    
    def unsanitize_email(self, sanitized_email: str) -> str:
        """Convert Firebase document ID back to email"""
        return sanitized_email.replace('_dot_', '.').replace('_at_', '@')