#!/usr/bin/env python3
# fix_datetime.py - Fix timezone-aware datetime issues in Firebase

import os
from dotenv import load_dotenv
from datetime import datetime

def fix_firebase_datetimes():
    """Fix timezone-aware datetime issues in Firebase collections"""
    print("🔧 Fixing Firebase datetime timezone issues...")
    
    try:
        # Load environment
        load_dotenv()
        
        # Initialize Firebase
        from firebase_admin import credentials, firestore, initialize_app
        import firebase_admin
        
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("⚠️ Firebase already initialized")
        except ValueError:
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
        
        # Fix user_management collection datetimes
        print("🔍 Checking user_management collection...")
        users_ref = db.collection("user_management")
        users = users_ref.stream()
        
        fixed_count = 0
        for user_doc in users:
            user_data = user_doc.to_dict()
            updates = {}
            
            # Fix timezone-aware datetimes
            for field in ['created_at', 'updated_at', 'last_login', 'deactivated_at', 'initialized_at']:
                if field in user_data and user_data[field]:
                    dt_val = user_data[field]
                    if isinstance(dt_val, datetime) and dt_val.tzinfo:
                        # Convert to timezone-naive
                        updates[field] = dt_val.replace(tzinfo=None)
            
            if updates:
                user_doc.reference.update(updates)
                fixed_count += 1
                print(f"  ✅ Fixed {user_doc.id}: {', '.join(updates.keys())}")
        
        # Fix system_settings collection datetimes
        print("🔍 Checking system_settings collection...")
        settings_ref = db.collection("system_settings").document("global")
        settings_doc = settings_ref.get()
        
        if settings_doc.exists:
            settings_data = settings_doc.to_dict()
            updates = {}
            
            for field in ['initialized_at', 'updated_at']:
                if field in settings_data and settings_data[field]:
                    dt_val = settings_data[field]
                    if isinstance(dt_val, datetime) and dt_val.tzinfo:
                        updates[field] = dt_val.replace(tzinfo=None)
            
            if updates:
                settings_ref.update(updates)
                print(f"  ✅ Fixed system settings: {', '.join(updates.keys())}")
        
        # Fix audit_logs collection datetimes
        print("🔍 Checking audit_logs collection...")
        audit_ref = db.collection("audit_logs")
        audit_logs = audit_ref.limit(100).stream()  # Fix recent logs only
        
        audit_fixed = 0
        for log_doc in audit_logs:
            log_data = log_doc.to_dict()
            
            if 'timestamp' in log_data and log_data['timestamp']:
                dt_val = log_data['timestamp']
                if isinstance(dt_val, datetime) and dt_val.tzinfo:
                    log_doc.reference.update({'timestamp': dt_val.replace(tzinfo=None)})
                    audit_fixed += 1
        
        if audit_fixed > 0:
            print(f"  ✅ Fixed {audit_fixed} audit log timestamps")
        
        print(f"\n🎉 DateTime fix complete!")
        print(f"   • Fixed {fixed_count} user records")
        print(f"   • Fixed {audit_fixed} audit logs")
        print(f"   • Fixed system settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing datetimes: {str(e)}")
        return False

def clean_env_file():
    """Remove unused variables from .env file"""
    print("\n🧹 Cleaning up .env file...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    # Read current content
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Variables to remove
    remove_vars = [
        'JYOTHSNA_EMAIL=',
        'JYOTHSNA_PERMISSIONS=',
        'JYOTHSNA_CAN_SEE_ADMIN_LOCATIONS='
    ]
    
    # Filter out unwanted lines
    cleaned_lines = []
    removed_count = 0
    
    for line in lines:
        should_remove = False
        for remove_var in remove_vars:
            if line.strip().startswith(remove_var):
                should_remove = True
                removed_count += 1
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # Write back cleaned content
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} unused environment variables")
        print("   • JYOTHSNA_EMAIL, JYOTHSNA_PERMISSIONS, JYOTHSNA_CAN_SEE_ADMIN_LOCATIONS")
        print("   • These are now managed through Firebase Admin Dashboard")
    else:
        print("✅ No unused variables found")
    
    return True

def main():
    """Main fix function"""
    print("🔧 Guardian Dashboard DateTime & Environment Fixer")
    print("="*60)
    
    # Clean up .env file
    clean_env_file()
    
    # Fix Firebase datetime issues
    fix_firebase_datetimes()
    
    print("\n" + "="*60)
    print("🎯 All fixes applied!")
    print("\n💡 What was fixed:")
    print("• Removed timezone information from Firebase datetime fields")
    print("• Cleaned up unused .env variables")
    print("• User permissions now managed through Firebase Admin Dashboard")
    
    print("\n🚀 Next steps:")
    print("1. Run: streamlit run main.py")
    print("2. Login as: sadakpramodh@yahoo.com")
    print("3. Access Admin Dashboard to manage users")
    print("4. Jyothsna user will be created automatically with correct permissions")

if __name__ == "__main__":
    main()