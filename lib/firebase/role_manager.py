"""
Firebase Role and User Management System
Handles user roles, permissions, and access control
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.message import EmailMessage
import os
from lib.firebase.manager import FirebaseManager
from lib.config.settings import GuardianConfig

class FirebaseRoleManager:
    """Firebase-based role and user management"""
    
    def __init__(self, firebase_manager: FirebaseManager, config: GuardianConfig):
        self.firebase = firebase_manager
        self.config = config
        self.db = firebase_manager.db
        self.user_mgmt_collection = "user_management"
        self.audit_collection = "audit_logs"
        self.settings_collection = "system_settings"
    
    def sanitize_email(self, email: str) -> str:
        """Convert email to Firebase-safe document ID"""
        return self.firebase.sanitize_email(email)
    
    def initialize_system(self, super_admin_email: str) -> bool:
        """Initialize the user management system with super admin"""
        try:
            # Check if super admin already exists
            sanitized_email = self.sanitize_email(super_admin_email)
            admin_doc = self.db.collection(self.user_mgmt_collection).document(sanitized_email).get()
            
            if not admin_doc.exists:
                # Create super admin user
                admin_data = {
                    "email": super_admin_email,
                    "sanitized_email": sanitized_email,
                    "role": "super_admin",
                    "permissions": {
                        "device_overview": True,
                        "locations": True,
                        "weather": True,
                        "call_logs": True,
                        "contacts": True,
                        "messages": True,
                        "phone_state": True
                    },
                    "can_see_users": ["*"],  # * means all users
                    "can_manage_users": True,
                    "can_see_features": ["*"],  # * means all features
                    "is_active": True,
                    "created_at": datetime.now(),
                    "created_by": "system",
                    "last_login": None,
                    "login_count": 0,
                    "notification_settings": {
                        "email_on_login": True,
                        "email_on_failed_login": True,
                        "email_on_permission_change": True
                    }
                }
                
                self.db.collection(self.user_mgmt_collection).document(sanitized_email).set(admin_data)
                
                # Initialize system settings
                self.initialize_system_settings()
                
                return True
            return False
        except Exception as e:
            st.error(f"Error initializing system: {str(e)}")
            return False
    
    def initialize_system_settings(self):
        """Initialize system-wide settings"""
        try:
            email_config = self.config.email_config
            
            settings_data = {
                "notification_email": email_config["username"],
                "login_notification_enabled": True,
                "audit_retention_days": 90,
                "max_login_attempts": 3,
                "session_timeout_minutes": 60,
                "require_email_verification": True,
                "system_initialized": True,
                "initialized_at": datetime.now(),
                "super_admin_email": self.config.super_admin_email
            }
            
            self.db.collection(self.settings_collection).document("global").set(settings_data)
            return True
        except Exception as e:
            st.error(f"Error initializing system settings: {str(e)}")
            return False
    
    def get_user_profile(self, email: str):
        """Get user profile from Firebase"""
        try:
            sanitized_email = self.sanitize_email(email)
            user_doc = self.db.collection(self.user_mgmt_collection).document(sanitized_email).get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            st.error(f"Error fetching user profile: {str(e)}")
            return None
    
    def can_access_feature(self, user_email: str, feature: str) -> bool:
        """Check if user can access a specific feature"""
        try:
            user_profile = self.get_user_profile(user_email)
            if not user_profile or not user_profile.get("is_active", False):
                return False
            
            # Check direct permissions
            permissions = user_profile.get("permissions", {})
            if permissions.get(feature, False):
                return True
            
            # Check if user has wildcard access
            can_see_features = user_profile.get("can_see_features", [])
            if "*" in can_see_features or feature in can_see_features:
                return True
            
            return False
        except Exception as e:
            return False
    
    def can_see_user_data(self, current_user_email: str, target_user_email: str) -> bool:
        """Check if current user can see target user's data"""
        try:
            current_user = self.get_user_profile(current_user_email)
            if not current_user:
                return False
            
            can_see_users = current_user.get("can_see_users", [])
            
            # Check if user can see all users or specific user
            return "*" in can_see_users or target_user_email in can_see_users
        except Exception as e:
            return False
    
    def get_accessible_users(self, current_user_email: str):
        """Get users that the current user can access"""
        try:
            current_user = self.get_user_profile(current_user_email)
            if not current_user:
                return []
            
            can_see_users = current_user.get("can_see_users", [])
            
            # If user can see all users (*)
            if "*" in can_see_users:
                return self.get_all_users()
            
            # Get specific users they can see
            accessible_users = []
            for email in can_see_users:
                user_profile = self.get_user_profile(email)
                if user_profile:
                    accessible_users.append(user_profile)
            
            return accessible_users
        except Exception as e:
            st.error(f"Error fetching accessible users: {str(e)}")
            return []
    
    def get_all_users(self):
        """Get all users from the system"""
        try:
            users_ref = self.db.collection(self.user_mgmt_collection)
            users = users_ref.stream()
            
            user_list = []
            for user_doc in users:
                user_data = user_doc.to_dict()
                user_list.append(user_data)
            
            return user_list
        except Exception as e:
            st.error(f"Error fetching users: {str(e)}")
            return []
    
    def is_super_admin(self, email: str) -> bool:
        """Check if user is super admin"""
        try:
            user_profile = self.get_user_profile(email)
            return user_profile and user_profile.get("role") == "super_admin"
        except Exception as e:
            return False
    
    def log_user_login(self, email: str, ip_address=None, user_agent=None, location=None):
        """Log user login and send notification"""
        try:
            # Update user login info
            sanitized_email = self.sanitize_email(email)
            user_ref = self.db.collection(self.user_mgmt_collection).document(sanitized_email)
            
            user_doc = user_ref.get()
            if user_doc.exists:
                current_data = user_doc.to_dict()
                login_count = current_data.get("login_count", 0) + 1
                
                user_ref.update({
                    "last_login": datetime.now(),
                    "login_count": login_count,
                    "last_ip": ip_address,
                    "last_user_agent": user_agent,
                    "last_location": location
                })
                
                # Log audit event
                self.log_audit_event("user_login", email, {
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "location": location,
                    "login_count": login_count
                })
                
                return True
            
            return False
        except Exception as e:
            st.error(f"Error logging user login: {str(e)}")
            return False
    
    def log_audit_event(self, event_type: str, user_email: str, details=None):
        """Log audit events to Firebase"""
        try:
            audit_data = {
                "event_type": event_type,
                "user_email": user_email,
                "timestamp": datetime.now(),
                "details": details or {},
                "session_id": st.session_state.get("session_id", "unknown")
            }
            
            # Add to audit collection
            self.db.collection(self.audit_collection).add(audit_data)
            
        except Exception as e:
            print(f"Error logging audit event: {str(e)}")
    
    def get_system_settings(self):
        """Get system-wide settings"""
        try:
            settings_doc = self.db.collection(self.settings_collection).document("global").get()
            if settings_doc.exists:
                return settings_doc.to_dict()
            return {}
        except Exception as e:
            return {}