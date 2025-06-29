#!/usr/bin/env python3
# quick_fix.py - Fix common environment issues

import os
import re

def fix_env_file():
    """Fix common issues in .env file"""
    print("🔧 Fixing .env file issues...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    
    # Read current .env content
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_applied = []
    
    # Fix 1: Add SUPER_ADMIN_EMAIL if missing
    if 'SUPER_ADMIN_EMAIL=' not in content:
        # Find a good place to insert it (after Firebase config)
        if 'FIREBASE_UNIVERSE_DOMAIN=' in content:
            content = content.replace(
                'FIREBASE_UNIVERSE_DOMAIN=googleapis.com',
                'FIREBASE_UNIVERSE_DOMAIN=googleapis.com\n\n# User Role Configuration\nSUPER_ADMIN_EMAIL=sadakpramodh@yahoo.com'
            )
            fixes_applied.append("Added SUPER_ADMIN_EMAIL")
        else:
            # Just append at the end
            content += '\n\n# User Role Configuration\nSUPER_ADMIN_EMAIL=sadakpramodh@yahoo.com\n'
            fixes_applied.append("Added SUPER_ADMIN_EMAIL")
    
    # Fix 2: Ensure FIREBASE_PRIVATE_KEY is properly quoted
    private_key_pattern = r'FIREBASE_PRIVATE_KEY=([^"\n]*-----BEGIN PRIVATE KEY-----[^"]*-----END PRIVATE KEY-----[^"\n]*)'
    if re.search(private_key_pattern, content):
        # Key is not quoted, fix it
        def quote_key(match):
            key_value = match.group(1).strip()
            return f'FIREBASE_PRIVATE_KEY="{key_value}"'
        
        content = re.sub(private_key_pattern, quote_key, content)
        fixes_applied.append("Fixed FIREBASE_PRIVATE_KEY quoting")
    
    # Fix 3: Ensure proper newline handling in private key
    private_key_quoted_pattern = r'FIREBASE_PRIVATE_KEY="([^"]*)"'
    match = re.search(private_key_quoted_pattern, content)
    if match:
        key_content = match.group(1)
        # If it doesn't have \n literals, add them
        if '\\n' not in key_content and '\n' in key_content:
            # Replace actual newlines with \n literals
            fixed_key = key_content.replace('\n', '\\n')
            content = content.replace(f'FIREBASE_PRIVATE_KEY="{key_content}"', f'FIREBASE_PRIVATE_KEY="{fixed_key}"')
            fixes_applied.append("Fixed FIREBASE_PRIVATE_KEY newline format")
    
    # Write back the fixed content
    if fixes_applied:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Applied fixes:")
        for fix in fixes_applied:
            print(f"   • {fix}")
        return True
    else:
        print("✅ No fixes needed")
        return True

def validate_private_key():
    """Validate Firebase private key format"""
    print("\n🔍 Validating Firebase private key format...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    private_key = os.getenv('FIREBASE_PRIVATE_KEY', '')
    
    if not private_key:
        print("❌ FIREBASE_PRIVATE_KEY is empty")
        return False
    
    # Check basic format
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
        print("❌ Private key doesn't start with -----BEGIN PRIVATE KEY-----")
        print("💡 Make sure the key includes the full header and footer")
        return False
    
    if not private_key.endswith('-----END PRIVATE KEY-----'):
        print("❌ Private key doesn't end with -----END PRIVATE KEY-----")
        print("💡 Make sure the key includes the full header and footer")
        return False
    
    # Check for proper newlines
    if '\\n' in private_key:
        print("✅ Private key uses literal \\n format (correct)")
    elif '\n' in private_key:
        print("⚠️ Private key uses actual newlines - this might cause issues")
        print("💡 Consider using literal \\n instead")
    
    print("✅ Private key format looks correct")
    return True

def create_test_firebase_connection():
    """Test Firebase connection with current configuration"""
    print("\n🔥 Testing Firebase connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from firebase_admin import credentials, firestore, initialize_app
        import firebase_admin
        
        # Check if already initialized
        try:
            firebase_admin.get_app()
            print("⚠️ Firebase already initialized - restarting Python might be needed")
            return True
        except ValueError:
            pass
        
        # Get credentials from environment
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
        
        # Check for missing required fields
        required_fields = ["project_id", "private_key", "client_email"]
        missing = [field for field in required_fields if not firebase_config.get(field)]
        
        if missing:
            print(f"❌ Missing Firebase fields: {', '.join(missing)}")
            return False
        
        # Try to initialize
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
        db = firestore.client()
        
        # Test a simple operation
        test_ref = db.collection("test_connection")
        
        print("✅ Firebase connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection failed: {str(e)}")
        
        if "MalformedFraming" in str(e):
            print("💡 This is usually a private key formatting issue:")
            print("   • Make sure the private key is wrapped in double quotes")
            print("   • Use literal \\n instead of actual newlines")
            print("   • Ensure the key starts and ends with the correct headers")
        
        return False

def main():
    """Run all fixes"""
    print("🔧 Guardian Dashboard Quick Fix Tool")
    print("="*50)
    
    # Run fixes
    fix_env_file()
    validate_private_key()
    create_test_firebase_connection()
    
    print("\n" + "="*50)
    print("🎯 Next Steps:")
    print("1. Run: python setup.py (to validate all fixes)")
    print("2. If Firebase still fails, restart your Python session")
    print("3. Run: streamlit run main.py")
    print("\n💡 If you still have issues:")
    print("• Check that your Firebase project has Firestore enabled")
    print("• Verify the service account has proper permissions")
    print("• Make sure the private key is copied exactly from Firebase")

if __name__ == "__main__":
    main()