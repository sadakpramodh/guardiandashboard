# 🛡️ Guardian Dashboard - Firebase Role Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![Firebase](https://img.shields.io/badge/Firebase-Admin_SDK-orange.svg)](https://firebase.google.com/)

A comprehensive, enterprise-grade device monitoring dashboard with advanced role-based access control, real-time analytics, and Firebase integration.

![Guardian Dashboard](https://img.shields.io/badge/Status-Production_Ready-green.svg)

## 🌟 Features

### 🔐 Advanced Security & Access Control
- **Role-Based Permissions**: Granular control over user access to features
- **Firebase Integration**: Complete user management stored in Firebase
- **Email OTP Authentication**: Secure login with time-limited OTP codes
- **Audit Logging**: Comprehensive tracking of all user activities
- **IP & Location Tracking**: Monitor login attempts with geolocation
- **Email Notifications**: Real-time alerts for logins and permission changes

### 📊 Comprehensive Device Monitoring
- **Device Overview**: Complete device metadata and system information
- **Location Tracking**: Interactive maps with path visualization and time filtering
- **Call Log Analytics**: Enhanced call analysis with type mapping and duration formatting
- **Message Management**: SMS tracking with type classification and search
- **Weather Dashboard**: Real-time weather data with trends and insights
- **Contact Management**: Complete contact list with search functionality
- **Phone State Monitoring**: Network status and connectivity tracking

### 👑 Super Admin Dashboard
- **User Management**: Create, edit, and deactivate users
- **Permission Control**: Dynamic permission assignment without code changes
- **System Analytics**: User activity insights and permission statistics
- **Audit Log Viewer**: Complete system activity monitoring
- **System Settings**: Configure notifications, retention policies, and security

### 🎯 Smart Analytics
- **Interactive Charts**: Plotly-powered visualizations
- **Trend Analysis**: Historical data patterns and insights
- **Real-time Metrics**: Live dashboard with key performance indicators
- **Export Capabilities**: Download reports and audit logs

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Firebase project with Firestore enabled
- Gmail account with App Password (for notifications)

### 1. Installation

```bash
# Clone the repository
git clone <your-repository-url>
cd guardian-dashboard

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root:

```bash
# Email Configuration for OTP Authentication
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Firebase Configuration
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your-client-cert-url
FIREBASE_UNIVERSE_DOMAIN=googleapis.com

# Super Admin Configuration
SUPER_ADMIN_EMAIL=your-admin@email.com

# Security Settings
ENABLE_ROLE_BASED_ACCESS=true
LOG_ACCESS_ATTEMPTS=true
```

### 3. Firebase Setup

1. **Create Firebase Project**: Go to [Firebase Console](https://console.firebase.google.com/)
2. **Enable Firestore**: Set up Cloud Firestore in your project
3. **Generate Service Account**: 
   - Go to Project Settings → Service Accounts
   - Generate new private key
   - Extract credentials to your `.env` file
4. **Set Firestore Rules**: Configure read/write permissions

### 4. Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"
   - Use this password in `MAIL_PASSWORD`

### 5. Run the Application

```bash
streamlit run main.py
```

The application will be available at `http://localhost:8501`

## 🔧 Configuration

### User Roles & Permissions

The system supports three main role types:

#### 🏰 Super Administrator
- **Email**: Configured in `SUPER_ADMIN_EMAIL`
- **Permissions**: Full system access
- **Capabilities**:
  - View all users and their devices
  - Manage user permissions
  - Access admin dashboard
  - System configuration
  - Audit log monitoring

#### 👤 Regular Users
- **Permissions**: Configurable per user through Firebase
- **Default Access**: Own device data only
- **Available Permissions**:
  - `device_overview` - Device information and metadata
  - `locations` - Location tracking and maps
  - `weather` - Weather data and analytics
  - `call_logs` - Call history and analytics
  - `contacts` - Contact list management
  - `messages` - SMS/message history
  - `phone_state` - Network and phone state monitoring

#### 🔗 Cross-User Access
Users can be granted access to view other users' data:
- Configurable through Admin Dashboard
- Granular control over which data types are accessible
- Real-time permission updates

### Email Notifications

Configure automatic notifications for:
- **Login Alerts**: User login with IP, location, and device info
- **Permission Changes**: When user permissions are modified
- **Failed Logins**: Security alerts for failed authentication attempts

## 📱 Usage Guide

### First Time Setup

1. **Super Admin Login**:
   - Use the email configured in `SUPER_ADMIN_EMAIL`
   - System automatically initializes on first login
   - Creates admin account and default settings

2. **Access Admin Dashboard**:
   - Login as super admin
   - Click "🛠️ Admin Dashboard" in sidebar
   - Complete system management interface

### User Management

1. **Create New User**:
   - Admin Dashboard → User Management → Create New User
   - Set email, role, permissions, and access rights
   - Configure notification preferences

2. **Modify Permissions**:
   - Select user from Admin Dashboard
   - Update permissions in real-time
   - Changes take effect immediately

3. **User Access Control**:
   - Set which users each person can view
   - Configure feature-level restrictions
   - Manage cross-user data access

### Device Monitoring

1. **Select User & Device**:
   - Choose from available users (based on permissions)
   - Select device from user's registered devices
   - Access authorized features only

2. **View Analytics**:
   - Interactive charts and visualizations
   - Real-time data updates
   - Export capabilities for reports

## 🏗️ Architecture

### System Components

```
Guardian Dashboard
├── Authentication Layer (OTP + Firebase)
├── Role Management System (Firebase-based)
├── Device Data Processing
├── Analytics Engine (Plotly)
├── Notification System (SMTP)
└── Audit System (Firebase)
```

### Firebase Collections

- **`user_management`**: User profiles, roles, and permissions
- **`audit_logs`**: Complete activity tracking
- **`system_settings`**: System-wide configuration
- **`users`**: Device data (existing, untouched)

### Security Features

- **Data Encryption**: All Firebase data encrypted at rest
- **Access Logging**: Every action logged with IP and timestamp
- **Session Management**: Secure session handling with timeout
- **Permission Validation**: Multi-layer permission checking

## 🔒 Security Best Practices

### Production Deployment

1. **Environment Variables**: Use secure environment variable management
2. **Firebase Rules**: Configure strict Firestore security rules
3. **HTTPS Only**: Always use HTTPS in production
4. **Regular Audits**: Monitor audit logs regularly
5. **Key Rotation**: Rotate Firebase service account keys periodically

### Recommended Firestore Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // User management collection - admin only
    match /user_management/{userId} {
      allow read, write: if request.auth != null && 
        get(/databases/$(database)/documents/user_management/$(request.auth.token.email.replace('@', '_at_').replace('.', '_dot_'))).data.role == 'super_admin';
    }
    
    // Audit logs - read only for admins
    match /audit_logs/{logId} {
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/user_management/$(request.auth.token.email.replace('@', '_at_').replace('.', '_dot_'))).data.role == 'super_admin';
      allow write: if request.auth != null;
    }
    
    // User data - based on permissions
    match /users/{userId}/{document=**} {
      allow read: if request.auth != null && 
        (userId == request.auth.token.email.replace('@', '_at_').replace('.', '_dot_') ||
         request.auth.token.email in get(/databases/$(database)/documents/user_management/$(request.auth.token.email.replace('@', '_at_').replace('.', '_dot_'))).data.can_see_users);
    }
  }
}
```

## 📊 Monitoring & Analytics

### Built-in Analytics

- **User Activity**: Login patterns, feature usage, session duration
- **System Performance**: Response times, error rates, data volume
- **Security Metrics**: Failed logins, permission changes, access patterns
- **Device Statistics**: Active devices, data collection rates, location tracking

### Custom Reports

Generate custom reports for:
- User access patterns
- Device activity summaries
- Security audit reports
- Permission change history

## 🛠️ Development

### Project Structure

```
guardian-dashboard/
├── main.py                     # Main application entry point
├── auth.py                     # Authentication system
├── firebase_role_manager.py    # Role management core
├── admin_management.py         # Admin interface
├── requirements.txt            # Python dependencies
├── .env                       # Environment configuration
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

### Adding New Features

1. **Create Feature Function**: Add to main.py or separate module
2. **Add Permission Check**: Use `role_manager.can_access_feature()`
3. **Update Admin Interface**: Add to permission management
4. **Test Access Control**: Verify permission enforcement

### API Integration

The system is designed for easy API integration:
- Firebase Admin SDK for database operations
- Plotly for advanced visualizations
- SMTP for email notifications
- IP geolocation for security tracking

## 🐛 Troubleshooting

### Common Issues

1. **Firebase Connection Error**:
   - Verify Firebase credentials in `.env`
   - Check service account permissions
   - Ensure Firestore is enabled

2. **Email Not Sending**:
   - Verify Gmail App Password
   - Check SMTP settings
   - Ensure 2FA is enabled on Gmail

3. **Permission Denied**:
   - Check user exists in `user_management` collection
   - Verify user is active
   - Check permission configuration

4. **Location Data Not Loading**:
   - Verify device data structure in Firebase
   - Check timestamp format (milliseconds)
   - Ensure proper collection path

### Debug Mode

Enable debug logging by setting:
```bash
LOG_ACCESS_ATTEMPTS=true
```

### Support

For technical support:
1. Check the troubleshooting section above
2. Review Firebase console for errors
3. Check application logs for specific error messages
4. Verify environment configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📮 Contact

For questions or support, please contact the development team.

---

**Guardian Dashboard** - Comprehensive device monitoring with enterprise-grade security 🛡️