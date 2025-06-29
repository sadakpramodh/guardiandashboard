# firebase_role_manager.py - Clean Firebase-based Role & User Management

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json
import requests
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

class FirebaseRoleManager:
    def __init__(self, db):
        self.db = db
        self.user_mgmt_collection = "user_management"
        self.audit_collection = "audit_logs"
        self.settings_collection = "system_settings"
        
    def sanitize_email(self, email):
        """Convert email to Firebase-safe document ID"""
        return email.replace('.', '_dot_').replace('@', '_at_') \
            .replace('/', '_').replace('[', '_').replace(']', '_') \
            .replace('*', '_').replace('?', '_')
    
    def unsanitize_email(self, sanitized_email):
        """Convert Firebase document ID back to email"""
        return sanitized_email.replace('_dot_', '.').replace('_at_', '@')
    
    def initialize_system(self, super_admin_email):
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
            # Use the email from .env for notifications
            notification_email = os.getenv("MAIL_USERNAME", "admin@example.com")
            
            settings_data = {
                "notification_email": notification_email,
                "login_notification_enabled": True,
                "audit_retention_days": 90,
                "max_login_attempts": 3,
                "session_timeout_minutes": 60,
                "require_email_verification": True,
                "system_initialized": True,
                "initialized_at": datetime.now(),
                "super_admin_email": os.getenv("SUPER_ADMIN_EMAIL", "sadakpramodh@yahoo.com")
            }
            
            self.db.collection(self.settings_collection).document("global").set(settings_data)
            return True
        except Exception as e:
            st.error(f"Error initializing system settings: {str(e)}")
            return False
    
    def get_user_profile(self, email):
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
    
    def create_user(self, user_data, created_by):
        """Create a new user with specified permissions"""
        try:
            sanitized_email = self.sanitize_email(user_data["email"])
            
            # Check if user already exists
            existing_user = self.db.collection(self.user_mgmt_collection).document(sanitized_email).get()
            if existing_user.exists:
                return False, "User already exists"
            
            # Set default user structure
            new_user_data = {
                "email": user_data["email"],
                "sanitized_email": sanitized_email,
                "role": user_data.get("role", "user"),
                "permissions": user_data.get("permissions", {
                    "device_overview": True,
                    "locations": True,
                    "weather": True,
                    "call_logs": False,
                    "contacts": False,
                    "messages": False,
                    "phone_state": False
                }),
                "can_see_users": user_data.get("can_see_users", [user_data["email"]]),
                "can_manage_users": user_data.get("can_manage_users", False),
                "can_see_features": user_data.get("can_see_features", []),
                "is_active": user_data.get("is_active", True),
                "created_at": datetime.now(),
                "created_by": created_by,
                "last_login": None,
                "login_count": 0,
                "notification_settings": user_data.get("notification_settings", {
                    "email_on_login": False,
                    "email_on_failed_login": False,
                    "email_on_permission_change": True
                }),
                "additional_info": user_data.get("additional_info", {})
            }
            
            # Save user to Firebase
            self.db.collection(self.user_mgmt_collection).document(sanitized_email).set(new_user_data)
            
            # Log the action
            self.log_audit_event("user_created", created_by, {
                "target_user": user_data["email"],
                "role": user_data.get("role", "user"),
                "permissions": new_user_data["permissions"]
            })
            
            return True, "User created successfully"
            
        except Exception as e:
            return False, f"Error creating user: {str(e)}"
    
    def update_user_permissions(self, target_email, new_permissions, updated_by):
        """Update user permissions"""
        try:
            sanitized_email = self.sanitize_email(target_email)
            user_ref = self.db.collection(self.user_mgmt_collection).document(sanitized_email)
            
            # Get current user data
            user_doc = user_ref.get()
            if not user_doc.exists:
                return False, "User not found"
            
            current_data = user_doc.to_dict()
            old_permissions = current_data.get("permissions", {})
            
            # Update permissions
            user_ref.update({
                "permissions": new_permissions,
                "updated_at": datetime.now(),
                "updated_by": updated_by
            })
            
            # Log the action
            self.log_audit_event("permissions_updated", updated_by, {
                "target_user": target_email,
                "old_permissions": old_permissions,
                "new_permissions": new_permissions
            })
            
            # Send notification if enabled
            if current_data.get("notification_settings", {}).get("email_on_permission_change", False):
                self.send_permission_change_notification(target_email, old_permissions, new_permissions)
            
            return True, "Permissions updated successfully"
            
        except Exception as e:
            return False, f"Error updating permissions: {str(e)}"
    
    def update_user_access(self, target_email, can_see_users, can_see_features, updated_by):
        """Update what users and features a user can access"""
        try:
            sanitized_email = self.sanitize_email(target_email)
            user_ref = self.db.collection(self.user_mgmt_collection).document(sanitized_email)
            
            user_ref.update({
                "can_see_users": can_see_users,
                "can_see_features": can_see_features,
                "updated_at": datetime.now(),
                "updated_by": updated_by
            })
            
            # Log the action
            self.log_audit_event("access_updated", updated_by, {
                "target_user": target_email,
                "can_see_users": can_see_users,
                "can_see_features": can_see_features
            })
            
            return True, "User access updated successfully"
            
        except Exception as e:
            return False, f"Error updating user access: {str(e)}"
    
    def deactivate_user(self, target_email, deactivated_by):
        """Deactivate a user account"""
        try:
            sanitized_email = self.sanitize_email(target_email)
            user_ref = self.db.collection(self.user_mgmt_collection).document(sanitized_email)
            
            user_ref.update({
                "is_active": False,
                "deactivated_at": datetime.now(),
                "deactivated_by": deactivated_by
            })
            
            # Log the action
            self.log_audit_event("user_deactivated", deactivated_by, {
                "target_user": target_email
            })
            
            return True, "User deactivated successfully"
            
        except Exception as e:
            return False, f"Error deactivating user: {str(e)}"
    
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
    
    def get_accessible_users(self, current_user_email):
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
    
    def can_access_feature(self, user_email, feature):
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
    
    def can_see_user_data(self, current_user_email, target_user_email):
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
    
    def log_user_login(self, email, ip_address=None, user_agent=None, location=None):
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
                
                # Send login notification if system setting is enabled
                settings = self.get_system_settings()
                if settings.get("login_notification_enabled", True):
                    self.send_login_notification(email, ip_address, user_agent, location)
                
                return True
            
            return False
        except Exception as e:
            st.error(f"Error logging user login: {str(e)}")
            return False
    
    def log_audit_event(self, event_type, user_email, details=None):
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
    
    def get_audit_logs(self, limit=100, event_type=None, user_email=None):
        """Get audit logs with optional filtering"""
        try:
            query = self.db.collection(self.audit_collection)
            
            if event_type:
                query = query.where("event_type", "==", event_type)
            
            if user_email:
                query = query.where("user_email", "==", user_email)
            
            query = query.order_by("timestamp", direction="DESCENDING").limit(limit)
            
            logs = query.stream()
            
            audit_logs = []
            for log_doc in logs:
                log_data = log_doc.to_dict()
                audit_logs.append(log_data)
            
            return audit_logs
        except Exception as e:
            st.error(f"Error fetching audit logs: {str(e)}")
            return []
    
    def send_login_notification(self, user_email, ip_address, user_agent, location):
        """Send email notification for user login"""
        try:
            # Get system settings for notification email
            settings = self.get_system_settings()
            notification_email = settings.get("notification_email", os.getenv("MAIL_USERNAME"))
            
            if not notification_email or not settings.get("login_notification_enabled", True):
                return
            
            # Prepare email content
            subject = f"🔐 Guardian Dashboard Login Alert - {user_email}"
            
            body = f"""
Hello Administrator,

A user has successfully logged into the Guardian Dashboard:

📧 User: {user_email}
🌐 IP Address: {ip_address or 'Unknown'}
💻 Device/Browser: {user_agent or 'Unknown'}
📍 Location: {location or 'Unknown'}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

If this login wasn't expected, please check the user's account immediately through the Admin Dashboard.

Best regards,
Guardian Dashboard System
            """
            
            self.send_email_notification(notification_email, subject, body)
            
        except Exception as e:
            print(f"Error sending login notification: {str(e)}")
    
    def send_permission_change_notification(self, user_email, old_permissions, new_permissions):
        """Send email notification for permission changes"""
        try:
            # Get system settings
            settings = self.get_system_settings()
            notification_email = settings.get("notification_email", os.getenv("MAIL_USERNAME"))
            
            if not notification_email:
                return
            
            # Compare permissions
            changes = []
            all_features = set(list(old_permissions.keys()) + list(new_permissions.keys()))
            
            for feature in all_features:
                old_val = old_permissions.get(feature, False)
                new_val = new_permissions.get(feature, False)
                
                if old_val != new_val:
                    status = "✅ GRANTED" if new_val else "❌ REVOKED"
                    changes.append(f"• {feature.replace('_', ' ').title()}: {status}")
            
            if not changes:
                return
            
            subject = f"🔄 Permission Update - {user_email}"
            body = f"""
Hello Administrator,

User permissions have been updated in the Guardian Dashboard:

📧 User: {user_email}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Permission Changes:
{chr(10).join(changes)}

You can review all user permissions in the Admin Dashboard.

Best regards,
Guardian Dashboard System
            """
            
            self.send_email_notification(notification_email, subject, body)
            
        except Exception as e:
            print(f"Error sending permission change notification: {str(e)}")
    
    def send_email_notification(self, to_email, subject, body):
        """Send email notification using SMTP"""
        try:
            # Email configuration from environment
            smtp_server = os.getenv("MAIL_SERVER")
            smtp_port = int(os.getenv("MAIL_PORT", 587))
            smtp_username = os.getenv("MAIL_USERNAME")
            smtp_password = os.getenv("MAIL_PASSWORD")
            from_email = os.getenv("MAIL_DEFAULT_SENDER")
            
            if not all([smtp_server, smtp_username, smtp_password, from_email]):
                print("Email configuration incomplete, skipping notification")
                return False
            
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email
            msg.set_content(body)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def get_system_settings(self):
        """Get system-wide settings"""
        try:
            settings_doc = self.db.collection(self.settings_collection).document("global").get()
            if settings_doc.exists:
                return settings_doc.to_dict()
            return {}
        except Exception as e:
            return {}
    
    def update_system_settings(self, settings_data, updated_by):
        """Update system-wide settings"""
        try:
            settings_ref = self.db.collection(self.settings_collection).document("global")
            
            settings_data.update({
                "updated_at": datetime.now(),
                "updated_by": updated_by
            })
            
            settings_ref.update(settings_data)
            
            # Log the action
            self.log_audit_event("system_settings_updated", updated_by, {
                "settings": settings_data
            })
            
            return True, "System settings updated successfully"
            
        except Exception as e:
            return False, f"Error updating system settings: {str(e)}"
    
    def is_super_admin(self, email):
        """Check if user is super admin"""
        try:
            user_profile = self.get_user_profile(email)
            return user_profile and user_profile.get("role") == "super_admin"
        except Exception as e:
            return False
    
    def cleanup_old_audit_logs(self):
        """Clean up old audit logs based on retention policy"""
        try:
            settings = self.get_system_settings()
            retention_days = settings.get("audit_retention_days", 90)
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Query old logs
            old_logs = self.db.collection(self.audit_collection) \
                .where("timestamp", "<", cutoff_date) \
                .stream()
            
            # Delete old logs in batches
            batch = self.db.batch()
            count = 0
            
            for log_doc in old_logs:
                batch.delete(log_doc.reference)
                count += 1
                
                if count >= 500:  # Firestore batch limit
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            if count > 0:
                batch.commit()
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up audit logs: {str(e)}")
            return False