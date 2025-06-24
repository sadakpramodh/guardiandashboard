#!/usr/bin/env python3
# setup.py - Guardian Dashboard Initial Setup Script

import os
import sys
from dotenv import load_dotenv

def check_requirements():
    """Check if all required dependencies are installed"""
    print("🔍 Checking system requirements...")
    
    try:
        import streamlit
        import firebase_admin
        import plotly
        import pandas
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n🔍 Checking environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("💡 Create a .env file based on the template in README.md")
        return False
    
    load_dotenv()
    
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == "":
            missing_vars.append(var)
    
    # Check for SUPER_ADMIN_EMAIL, but provide default if missing
    super_admin = os.getenv('SUPER_ADMIN_EMAIL')
    if not super_admin:
        print("⚠️ SUPER_ADMIN_EMAIL not set, will use default: sadakpramodh@yahoo.com")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Check your .env file and ensure all required variables are set")
        
        # Specific help for Firebase private key
        if 'FIREBASE_PRIVATE_KEY' in missing_vars:
            print("\n🔧 Firebase Private Key Fix:")
            print('• Make sure FIREBASE_PRIVATE_KEY is wrapped in double quotes')
            print('• Example: FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nYOUR_KEY_HERE\\n-----END PRIVATE KEY-----\\n"')
            print('• The \\n should be literal backslash-n, not actual newlines')
        
        return False
    
    # Check if private key is properly formatted
    private_key = os.getenv('FIREBASE_PRIVATE_KEY', '')
    if private_key and not private_key.startswith('"-----BEGIN PRIVATE KEY-----'):
        print("⚠️ Firebase private key may not be properly formatted")
        print('💡 Ensure it starts with "-----BEGIN PRIVATE KEY----- and ends with -----END PRIVATE KEY-----"')
        print('💡 Use literal \\n for newlines, not actual newlines')
    
    print("✅ Environment configuration looks good")
    return True

def check_firebase_connection():
    """Test Firebase connection"""
    print("\n🔍 Testing Firebase connection...")
    
    try:
        from firebase_admin import credentials, firestore, initialize_app
        import firebase_admin
        
        # Check if Firebase is already initialized
        try:
            firebase_admin.get_app()
            print("✅ Firebase already initialized")
            return True
        except ValueError:
            pass
        
        # Initialize Firebase
        firebase_config = {
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
        
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
        db = firestore.client()
        
        # Test connection by trying to access a collection
        test_ref = db.collection("test_connection")
        
        print("✅ Firebase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {str(e)}")
        print("💡 Check your Firebase credentials in .env file")
        print("💡 Ensure Firestore is enabled in your Firebase project")
        return False

def check_email_config():
    """Test email configuration"""
    print("\n🔍 Testing email configuration...")
    
    try:
        import smtplib
        from email.message import EmailMessage
        
        smtp_server = os.getenv("MAIL_SERVER")
        smtp_port = int(os.getenv("MAIL_PORT", 587))
        smtp_username = os.getenv("MAIL_USERNAME")
        smtp_password = os.getenv("MAIL_PASSWORD")
        
        # Test SMTP connection
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
        
        print("✅ Email configuration successful")
        return True
        
    except Exception as e:
        print(f"❌ Email configuration failed: {str(e)}")
        print("💡 Check your email credentials in .env file")
        print("💡 For Gmail, make sure you're using an App Password, not your regular password")
        print("💡 Enable 2-Factor Authentication and generate an App Password")
        return False

def print_setup_summary():
    """Print setup summary and next steps"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Run the application: streamlit run main.py")
    print("2. Open your browser to: http://localhost:8501")
    print(f"3. Login with super admin email: {os.getenv('SUPER_ADMIN_EMAIL')}")
    print("4. Use the OTP sent to your email to authenticate")
    print("5. System will auto-initialize on first super admin login")
    print("6. Access Admin Dashboard to manage users and permissions")
    
    print("\n📧 Email Notifications:")
    print(f"• Notifications will be sent to: {os.getenv('MAIL_USERNAME')}")
    print("• Login alerts, permission changes, and security notifications")
    
    print("\n🔐 Default Users:")
    print(f"• Super Admin: {os.getenv('SUPER_ADMIN_EMAIL')} (Full Access)")
    print(f"• Jyothsna: {os.getenv('JYOTHSNA_EMAIL', 'jyothsnaroyal944@gmail.com')} (Limited Access)")
    
    print("\n🛡️ Security Features:")
    print("• Role-based access control")
    print("• Firebase-based user management")
    print("• Complete audit logging")
    print("• IP and location tracking")
    print("• Email notifications for all activities")
    
    print("\n💡 Tips:")
    print("• Access Admin Dashboard as super admin to manage users")
    print("• All permissions are configurable through Firebase")
    print("• Check audit logs for security monitoring")
    print("• Email notifications can be configured per user")

def main():
    """Main setup function"""
    print("🛡️ Guardian Dashboard Setup Script")
    print("="*50)
    
    # Run all checks
    checks = [
        check_requirements,
        check_env_file,
        check_firebase_connection,
        check_email_config
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        print_setup_summary()
        return 0
    else:
        print("\n❌ Setup incomplete. Please fix the issues above and run setup again.")
        print("💡 For help, check the README.md file or the troubleshooting section")
        return 1

if __name__ == "__main__":
    sys.exit(main())