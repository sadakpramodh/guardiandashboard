# admin_management.py - Super Admin Management Interface

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from firebase_role_manager import FirebaseRoleManager

def show_admin_dashboard(db, current_user_email):
    """Super Admin Dashboard for User & Role Management"""
    
    role_manager = FirebaseRoleManager(db)
    
    # Initialize system if needed
    if not role_manager.get_user_profile(current_user_email):
        if st.button("🚀 Initialize System"):
            if role_manager.initialize_system(current_user_email):
                st.success("✅ System initialized successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize system")
        return
    
    st.title("👑 Super Admin Dashboard")
    st.markdown("---")
    
    # Admin tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 User Management", 
        "🔐 Role & Permissions", 
        "📊 System Analytics", 
        "🔍 Audit Logs", 
        "⚙️ System Settings"
    ])
    
    with tab1:
        show_user_management(role_manager, current_user_email)
    
    with tab2:
        show_role_permissions_management(role_manager, current_user_email)
    
    with tab3:
        show_system_analytics(role_manager)
    
    with tab4:
        show_audit_logs(role_manager)
    
    with tab5:
        show_system_settings(role_manager, current_user_email)

def show_user_management(role_manager, current_user_email):
    """User Management Interface"""
    
    st.subheader("👥 User Management")
    
    # Create new user section
    with st.expander("➕ Create New User"):
        with st.form("create_user_form"):
            st.markdown("### Add New User")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_email = st.text_input("📧 Email Address", placeholder="user@example.com")
                new_role = st.selectbox("👤 Role", ["user", "admin", "manager", "viewer"])
                
            with col2:
                is_active = st.checkbox("✅ Active", value=True)
                can_manage_users = st.checkbox("🔧 Can Manage Users", value=False)
            
            st.markdown("#### 🔐 Permissions")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                device_overview = st.checkbox("📱 Device Overview", value=True)
                locations = st.checkbox("🌍 Locations", value=True)
            
            with col2:
                weather = st.checkbox("🌦️ Weather", value=True)
                call_logs = st.checkbox("📞 Call Logs", value=False)
            
            with col3:
                contacts = st.checkbox("👥 Contacts", value=False)
                messages = st.checkbox("💬 Messages", value=False)
            
            with col4:
                phone_state = st.checkbox("📶 Phone State", value=False)
                
            st.markdown("#### 👁️ User Access")
            access_mode = st.radio(
                "Who can this user see?",
                ["Own data only", "Specific users", "All users"],
                horizontal=True
            )
            
            specific_users = []
            if access_mode == "Specific users":
                all_users = role_manager.get_all_users()
                user_emails = [user["email"] for user in all_users if user["email"] != new_email]
                specific_users = st.multiselect("Select users this user can access:", user_emails)
            
            st.markdown("#### 📧 Notification Settings")
            email_on_login = st.checkbox("📬 Email on Login", value=False)
            email_on_failed_login = st.checkbox("⚠️ Email on Failed Login", value=False)
            email_on_permission_change = st.checkbox("🔄 Email on Permission Change", value=True)
            
            submitted = st.form_submit_button("✅ Create User", use_container_width=True)
            
            if submitted and new_email:
                # Prepare user data
                permissions = {
                    "device_overview": device_overview,
                    "locations": locations,
                    "weather": weather,
                    "call_logs": call_logs,
                    "contacts": contacts,
                    "messages": messages,
                    "phone_state": phone_state
                }
                
                can_see_users = []
                if access_mode == "Own data only":
                    can_see_users = [new_email]
                elif access_mode == "Specific users":
                    can_see_users = specific_users + [new_email]  # Always include themselves
                elif access_mode == "All users":
                    can_see_users = ["*"]
                
                user_data = {
                    "email": new_email,
                    "role": new_role,
                    "permissions": permissions,
                    "can_see_users": can_see_users,
                    "can_manage_users": can_manage_users,
                    "is_active": is_active,
                    "notification_settings": {
                        "email_on_login": email_on_login,
                        "email_on_failed_login": email_on_failed_login,
                        "email_on_permission_change": email_on_permission_change
                    }
                }
                
                success, message = role_manager.create_user(user_data, current_user_email)
                
                if success:
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Existing users list
    st.markdown("### 📋 Existing Users")
    
    all_users = role_manager.get_all_users()
    
    if not all_users:
        st.info("No users found in the system.")
        return
    
    # Create DataFrame for better display
    users_data = []
    for user in all_users:
        user_info = {
            "Email": user.get("email", ""),
            "Role": user.get("role", "").title(),
            "Status": "🟢 Active" if user.get("is_active", False) else "🔴 Inactive",
            "Last Login": user.get("last_login", "Never"),
            "Login Count": user.get("login_count", 0),
            "Can Manage Users": "✅" if user.get("can_manage_users", False) else "❌",
            "Permissions": len([k for k, v in user.get("permissions", {}).items() if v]),
            "Can See Users": len(user.get("can_see_users", [])) if user.get("can_see_users") != ["*"] else "All"
        }
        users_data.append(user_info)
    
    users_df = pd.DataFrame(users_data)
    
    # Display users table
    st.dataframe(users_df, use_container_width=True)
    
    # User action buttons
    st.markdown("### 🔧 User Actions")
    
    selected_user_email = st.selectbox(
        "Select user to manage:",
        [user["email"] for user in all_users],
        key="user_action_select"
    )
    
    if selected_user_email:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ Edit Permissions", use_container_width=True):
                st.session_state.edit_user_email = selected_user_email
                st.session_state.show_edit_form = True
        
        with col2:
            if st.button("🔄 Reset Password", use_container_width=True):
                st.info("Password reset functionality would be implemented here")
        
        with col3:
            if st.button("🚫 Deactivate User", use_container_width=True):
                if role_manager.deactivate_user(selected_user_email, current_user_email)[0]:
                    st.success("User deactivated successfully!")
                    st.rerun()

def show_role_permissions_management(role_manager, current_user_email):
    """Role and Permissions Management Interface"""
    
    st.subheader("🔐 Role & Permissions Management")
    
    all_users = role_manager.get_all_users()
    
    if not all_users:
        st.info("No users found in the system.")
        return
    
    # Select user to edit
    selected_user = st.selectbox(
        "👤 Select User to Edit:",
        [user["email"] for user in all_users],
        key="permissions_user_select"
    )
    
    if selected_user:
        user_profile = role_manager.get_user_profile(selected_user)
        
        if user_profile:
            st.markdown(f"### Editing: **{selected_user}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔐 Feature Permissions")
                current_permissions = user_profile.get("permissions", {})
                
                new_permissions = {}
                new_permissions["device_overview"] = st.checkbox(
                    "📱 Device Overview", 
                    value=current_permissions.get("device_overview", False),
                    key="edit_device_overview"
                )
                new_permissions["locations"] = st.checkbox(
                    "🌍 Locations", 
                    value=current_permissions.get("locations", False),
                    key="edit_locations"
                )
                new_permissions["weather"] = st.checkbox(
                    "🌦️ Weather", 
                    value=current_permissions.get("weather", False),
                    key="edit_weather"
                )
                new_permissions["call_logs"] = st.checkbox(
                    "📞 Call Logs", 
                    value=current_permissions.get("call_logs", False),
                    key="edit_call_logs"
                )
                new_permissions["contacts"] = st.checkbox(
                    "👥 Contacts", 
                    value=current_permissions.get("contacts", False),
                    key="edit_contacts"
                )
                new_permissions["messages"] = st.checkbox(
                    "💬 Messages", 
                    value=current_permissions.get("messages", False),
                    key="edit_messages"
                )
                new_permissions["phone_state"] = st.checkbox(
                    "📶 Phone State", 
                    value=current_permissions.get("phone_state", False),
                    key="edit_phone_state"
                )
            
            with col2:
                st.markdown("#### 👁️ User Access Control")
                
                current_can_see = user_profile.get("can_see_users", [])
                
                if "*" in current_can_see:
                    current_access_mode = "All users"
                elif len(current_can_see) == 1 and current_can_see[0] == selected_user:
                    current_access_mode = "Own data only"
                else:
                    current_access_mode = "Specific users"
                
                access_mode = st.radio(
                    "Who can this user see?",
                    ["Own data only", "Specific users", "All users"],
                    index=["Own data only", "Specific users", "All users"].index(current_access_mode),
                    key="edit_access_mode"
                )
                
                new_can_see_users = []
                if access_mode == "Own data only":
                    new_can_see_users = [selected_user]
                elif access_mode == "Specific users":
                    other_users = [user["email"] for user in all_users if user["email"] != selected_user]
                    current_specific = [email for email in current_can_see if email != selected_user and email != "*"]
                    
                    selected_users = st.multiselect(
                        "Select users this user can access:",
                        other_users,
                        default=current_specific,
                        key="edit_specific_users"
                    )
                    new_can_see_users = selected_users + [selected_user]
                elif access_mode == "All users":
                    new_can_see_users = ["*"]
                
                st.markdown("#### 🔧 Management Permissions")
                can_manage_users = st.checkbox(
                    "Can Manage Other Users",
                    value=user_profile.get("can_manage_users", False),
                    key="edit_can_manage"
                )
                
                st.markdown("#### 📧 Notification Settings")
                current_notifications = user_profile.get("notification_settings", {})
                
                email_on_login = st.checkbox(
                    "📬 Email on Login",
                    value=current_notifications.get("email_on_login", False),
                    key="edit_email_login"
                )
                email_on_failed_login = st.checkbox(
                    "⚠️ Email on Failed Login",
                    value=current_notifications.get("email_on_failed_login", False),
                    key="edit_email_failed"
                )
                email_on_permission_change = st.checkbox(
                    "🔄 Email on Permission Change",
                    value=current_notifications.get("email_on_permission_change", True),
                    key="edit_email_permissions"
                )
            
            # Update buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Update Permissions", use_container_width=True):
                    success, message = role_manager.update_user_permissions(
                        selected_user, new_permissions, current_user_email
                    )
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            with col2:
                if st.button("🔄 Update Access & Settings", use_container_width=True):
                    # Update user access
                    success1, message1 = role_manager.update_user_access(
                        selected_user, new_can_see_users, [], current_user_email
                    )
                    
                    # Update notification settings
                    sanitized_email = role_manager.sanitize_email(selected_user)
                    user_ref = role_manager.db.collection(role_manager.user_mgmt_collection).document(sanitized_email)
                    
                    try:
                        user_ref.update({
                            "can_manage_users": can_manage_users,
                            "notification_settings": {
                                "email_on_login": email_on_login,
                                "email_on_failed_login": email_on_failed_login,
                                "email_on_permission_change": email_on_permission_change
                            },
                            "updated_at": datetime.now(),
                            "updated_by": current_user_email
                        })
                        success2 = True
                        message2 = "Settings updated successfully"
                    except Exception as e:
                        success2 = False
                        message2 = f"Error updating settings: {str(e)}"
                    
                    if success1 and success2:
                        st.success("✅ Access and settings updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message1 if not success1 else message2}")

def show_system_analytics(role_manager):
    """System Analytics Dashboard"""
    
    st.subheader("📊 System Analytics")
    
    # Get all users
    all_users = role_manager.get_all_users()
    
    if not all_users:
        st.info("No data available for analytics.")
        return
    
    # User statistics
    col1, col2, col3, col4 = st.columns(4)
    
    active_users = len([u for u in all_users if u.get("is_active", False)])
    total_users = len(all_users)
    super_admins = len([u for u in all_users if u.get("role") == "super_admin"])
    recent_logins = len([u for u in all_users if u.get("last_login") and 
                        isinstance(u.get("last_login"), datetime) and
                        (datetime.now() - u.get("last_login").replace(tzinfo=None) if u.get("last_login").tzinfo else datetime.now() - u.get("last_login")).days <= 7])
    
    with col1:
        st.metric("👥 Total Users", total_users)
    with col2:
        st.metric("🟢 Active Users", active_users)
    with col3:
        st.metric("👑 Super Admins", super_admins)
    with col4:
        st.metric("📅 Recent Logins (7d)", recent_logins)
    
    # User role distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👤 User Role Distribution")
        role_counts = {}
        for user in all_users:
            role = user.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        
        if role_counts:
            fig_roles = px.pie(
                values=list(role_counts.values()),
                names=list(role_counts.keys()),
                title="User Roles"
            )
            st.plotly_chart(fig_roles, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 User Activity Status")
        status_counts = {"Active": active_users, "Inactive": total_users - active_users}
        
        fig_status = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="User Status",
            color_discrete_map={"Active": "green", "Inactive": "red"}
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Permission analysis
    st.markdown("#### 🔐 Permission Analysis")
    
    permission_stats = {}
    for user in all_users:
        permissions = user.get("permissions", {})
        for perm, granted in permissions.items():
            if perm not in permission_stats:
                permission_stats[perm] = {"granted": 0, "total": 0}
            permission_stats[perm]["total"] += 1
            if granted:
                permission_stats[perm]["granted"] += 1
    
    perm_data = []
    for perm, stats in permission_stats.items():
        perm_data.append({
            "Permission": perm.replace("_", " ").title(),
            "Granted": stats["granted"],
            "Total Users": stats["total"],
            "Percentage": (stats["granted"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        })
    
    perm_df = pd.DataFrame(perm_data)
    
    if not perm_df.empty:
        fig_perms = px.bar(
            perm_df,
            x="Permission",
            y="Granted",
            title="Permissions Granted Across Users",
            text="Percentage"
        )
        fig_perms.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_perms, use_container_width=True)
    
    # Recent user activity
    st.markdown("#### 📅 Recent User Activity")
    
    recent_users = []
    for user in all_users:
        last_login = user.get("last_login")
        if last_login and isinstance(last_login, datetime):
            # Handle timezone-aware datetimes
            if last_login.tzinfo:
                last_login = last_login.replace(tzinfo=None)
            
            recent_users.append({
                "Email": user["email"],
                "Last Login": last_login,
                "Login Count": user.get("login_count", 0),
                "Role": user.get("role", "").title(),
                "Status": "Active" if user.get("is_active", False) else "Inactive"
            })
    
    if recent_users:
        recent_df = pd.DataFrame(recent_users)
        recent_df = recent_df.sort_values("Last Login", ascending=False)
        st.dataframe(recent_df, use_container_width=True)
    else:
        st.info("No recent login activity found.")

def show_audit_logs(role_manager):
    """Audit Logs Viewer"""
    
    st.subheader("🔍 Audit Logs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        event_types = ["", "user_login", "user_created", "permissions_updated", 
                      "access_updated", "user_deactivated", "system_settings_updated"]
        selected_event_type = st.selectbox("Event Type", event_types)
    
    with col2:
        all_users = role_manager.get_all_users()
        user_emails = [""] + [user["email"] for user in all_users]
        selected_user = st.selectbox("User", user_emails)
    
    with col3:
        log_limit = st.selectbox("Number of Records", [50, 100, 200, 500], index=1)
    
    # Fetch and display logs
    audit_logs = role_manager.get_audit_logs(
        limit=log_limit,
        event_type=selected_event_type if selected_event_type else None,
        user_email=selected_user if selected_user else None
    )
    
    if audit_logs:
        # Convert to DataFrame for better display
        logs_data = []
        for log in audit_logs:
            logs_data.append({
                "Timestamp": log.get("timestamp", datetime.now()),
                "Event Type": log.get("event_type", "").replace("_", " ").title(),
                "User": log.get("user_email", ""),
                "Details": str(log.get("details", {}))[:100] + "..." if len(str(log.get("details", {}))) > 100 else str(log.get("details", {}))
            })
        
        logs_df = pd.DataFrame(logs_data)
        st.dataframe(logs_df, use_container_width=True)
        
        # Export option
        if st.button("📥 Export Audit Logs"):
            csv = logs_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No audit logs found matching the selected criteria.")
    
    # Audit log analytics
    if audit_logs:
        st.markdown("#### 📊 Audit Log Analytics")
        
        # Event type distribution
        event_counts = {}
        for log in audit_logs:
            event_type = log.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        if event_counts:
            fig_events = px.bar(
                x=list(event_counts.keys()),
                y=list(event_counts.values()),
                title="Event Type Distribution",
                labels={"x": "Event Type", "y": "Count"}
            )
            st.plotly_chart(fig_events, use_container_width=True)

def show_system_settings(role_manager, current_user_email):
    """System Settings Management"""
    
    st.subheader("⚙️ System Settings")
    
    # Get current settings
    current_settings = role_manager.get_system_settings()
    
    with st.form("system_settings_form"):
        st.markdown("#### 📧 Notification Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            notification_email = st.text_input(
                "Notification Email",
                value=current_settings.get("notification_email", ""),
                help="Email address to receive system notifications"
            )
            
            login_notification_enabled = st.checkbox(
                "Enable Login Notifications",
                value=current_settings.get("login_notification_enabled", True)
            )
        
        with col2:
            audit_retention_days = st.number_input(
                "Audit Log Retention (Days)",
                min_value=30,
                max_value=365,
                value=current_settings.get("audit_retention_days", 90)
            )
            
            max_login_attempts = st.number_input(
                "Max Login Attempts",
                min_value=3,
                max_value=10,
                value=current_settings.get("max_login_attempts", 3)
            )
        
        st.markdown("#### 🔐 Security Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            session_timeout_minutes = st.number_input(
                "Session Timeout (Minutes)",
                min_value=15,
                max_value=480,
                value=current_settings.get("session_timeout_minutes", 60)
            )
        
        with col2:
            require_email_verification = st.checkbox(
                "Require Email Verification",
                value=current_settings.get("require_email_verification", True)
            )
        
        # Submit button
        submitted = st.form_submit_button("💾 Update Settings", use_container_width=True)
        
        if submitted:
            new_settings = {
                "notification_email": notification_email,
                "login_notification_enabled": login_notification_enabled,
                "audit_retention_days": audit_retention_days,
                "max_login_attempts": max_login_attempts,
                "session_timeout_minutes": session_timeout_minutes,
                "require_email_verification": require_email_verification
            }
            
            success, message = role_manager.update_system_settings(new_settings, current_user_email)
            
            if success:
                st.success(f"✅ {message}")
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    # System maintenance
    st.markdown("#### 🧹 System Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Cleanup Old Audit Logs", use_container_width=True):
            if role_manager.cleanup_old_audit_logs():
                st.success("✅ Old audit logs cleaned up successfully!")
            else:
                st.error("❌ Failed to cleanup audit logs")
    
    with col2:
        if st.button("📊 System Health Check", use_container_width=True):
            st.info("System health check functionality would be implemented here")
    
    # Display current system info
    st.markdown("#### ℹ️ System Information")
    
    system_info = {
        "System Initialized": current_settings.get("system_initialized", False),
        "Initialization Date": current_settings.get("initialized_at", "Unknown"),
        "Total Users": len(role_manager.get_all_users()),
        "Active Users": len([u for u in role_manager.get_all_users() if u.get("is_active", False)]),
        "Last Settings Update": current_settings.get("updated_at", "Never"),
        "Updated By": current_settings.get("updated_by", "Unknown")
    }
    
    info_df = pd.DataFrame(list(system_info.items()), columns=["Setting", "Value"])
    st.dataframe(info_df, use_container_width=True, hide_index=True)