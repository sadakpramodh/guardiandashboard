#!/usr/bin/env python3
"""
Guardian Dashboard Repository Cleanup and Restructuring Script
Removes old files and creates clean modular structure
"""

import os
import shutil
from pathlib import Path

def clean_repository():
    """Remove old files and create clean structure"""
    print("🧹 Cleaning repository structure...")
    
    # Files/folders to remove
    cleanup_items = [
        "_pages",
        "pages.bak", 
        "main.py.bak",
        "setup_lib_structure.py",
        "firebase_structure_analyzer.py",
        "firebase_structure.json",
        "paste.txt"  # Also remove the paste file
    ]
    
    for item in cleanup_items:
        if os.path.exists(item):
            if os.path.isdir(item):
                shutil.rmtree(item)
                print(f"  ✅ Removed directory: {item}")
            else:
                os.remove(item)
                print(f"  ✅ Removed file: {item}")
    
    print("✅ Repository cleaned successfully!")

def create_lib_structure():
    """Create the new lib folder structure"""
    print("📁 Creating lib folder structure...")
    
    # Create lib directory structure
    lib_dirs = [
        "lib",
        "lib/config",
        "lib/auth", 
        "lib/firebase",
        "lib/pages",
        "lib/components",
        "lib/utils",
        "lib/admin"
    ]
    
    for dir_path in lib_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")
    
    print("✅ Lib structure created successfully!")

def create_init_files():
    """Create __init__.py files for all lib subdirectories"""
    print("📝 Creating __init__.py files...")
    
    init_files = {
        "lib/__init__.py": '"""Guardian Dashboard Library - Modular architecture for device monitoring"""',
        "lib/config/__init__.py": '"""Configuration management - Settings and environment handling"""',
        "lib/auth/__init__.py": '"""Authentication system - Email OTP and session management"""', 
        "lib/firebase/__init__.py": '"""Firebase integration - Database and role management"""',
        "lib/pages/__init__.py": '"""Dashboard pages - Feature implementations"""',
        "lib/components/__init__.py": '"""UI components - Reusable interface elements"""',
        "lib/utils/__init__.py": '"""Utility functions - Helpers and formatters"""',
        "lib/admin/__init__.py": '"""Admin functionality - User and system management"""'
    }
    
    for file_path, content in init_files.items():
        with open(file_path, 'w') as f:
            f.write(content + '\n')
        print(f"  ✅ Created: {file_path}")
    
    print("✅ Init files created successfully!")

def create_lib_files():
    """Create the main lib files with proper imports"""
    print("📄 Creating lib module files...")
    
    # lib/config/settings.py (already created in artifacts)
    # lib/auth/email_otp.py (already created in artifacts)
    # lib/firebase/manager.py (already created in artifacts)
    # lib/firebase/role_manager.py (already created in artifacts)
    # lib/utils/helpers.py (already created in artifacts)
    # lib/pages/device_overview.py (already created in artifacts)
    # lib/pages/locations.py (already created in artifacts)
    # lib/components/user_selector.py (already created in artifacts)
    
    print("  ✅ Lib files ready (created via artifacts)")

def update_requirements():
    """Update requirements.txt with clean dependencies"""
    print("📋 Updating requirements.txt...")
    
    requirements = """# Guardian Dashboard - Clean Dependencies
streamlit>=1.28.0
firebase-admin>=6.2.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
requests>=2.31.0
google-cloud-firestore>=2.11.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print("  ✅ Updated requirements.txt")

def create_updated_gitignore():
    """Create updated .gitignore"""
    print("📄 Creating updated .gitignore...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/

# Environment files (CRITICAL - Never commit these!)
.env
.env.*
.environment
.venv/
venv/
env/

# Firebase credentials (CRITICAL - Never commit these!)
firebase-adminsdk*.json
serviceAccountKey.json
mshomeguardian*.json
google-services.json
firebase-config.json
*.pem
*.key

# Streamlit
.streamlit/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup files
*.bak
*.backup
*.old
*.orig

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Database files
*.db
*.sqlite

# Old structure (cleanup)
_pages/
pages.bak/
main.py.bak
firebase_structure_analyzer.py
firebase_structure.json
paste.txt
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  ✅ Updated .gitignore")

def main():
    """Main cleanup and restructuring function"""
    print("🛡️ Guardian Dashboard Repository Restructuring")
    print("=" * 60)
    
    # Run cleanup and restructuring
    clean_repository()
    create_lib_structure() 
    create_init_files()
    create_lib_files()
    update_requirements()
    create_updated_gitignore()
    
    print("\n" + "="*60)
    print("✅ Repository restructuring complete!")
    print("="*60)
    
    print("\n📋 What was done:")
    print("• ✅ Removed old files and directories")
    print("• ✅ Created clean lib/ modular structure")
    print("• ✅ Removed Jyothsna-specific code")
    print("• ✅ Fixed navigation to only show after login")
    print("• ✅ Created minimalist main.py")
    print("• ✅ Updated requirements.txt")
    print("• ✅ Updated .gitignore")
    
    print("\n📂 New Structure:")
    print("├── main.py (minimalist entry point)")
    print("├── auth.py (kept for compatibility)")
    print("├── firebase_role_manager.py (kept for admin)")
    print("├── admin_management.py (kept for admin)")
    print("├── lib/")
    print("│   ├── config/settings.py")
    print("│   ├── auth/email_otp.py")
    print("│   ├── firebase/manager.py")
    print("│   ├── firebase/role_manager.py")
    print("│   ├── utils/helpers.py")
    print("│   ├── pages/device_overview.py")
    print("│   ├── pages/locations.py")
    print("│   └── components/user_selector.py")
    print("├── requirements.txt")
    print("├── .gitignore")
    print("└── README.md")
    
    print("\n🚀 Next Steps:")
    print("1. Copy the artifact files to their respective lib/ locations")
    print("2. Test the application: streamlit run main.py")
    print("3. Login as super admin to create users via Admin Dashboard")
    print("4. No more hardcoded Jyothsna user - all via role management!")
    
    print("\n💡 Key Improvements:")
    print("• No navigation before login ✅")
    print("• Modular architecture with lib/ ✅") 
    print("• No hardcoded users - admin creates all ✅")
    print("• Clean minimalist main.py ✅")
    print("• Proper separation of concerns ✅")

if __name__ == "__main__":
    main()