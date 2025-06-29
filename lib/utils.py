# lib/utils.py
"""
Utility functions for Guardian Dashboard
"""

import pandas as pd
import requests
from datetime import datetime

def format_duration(seconds):
    """Convert seconds to minutes and seconds format"""
    if pd.isna(seconds) or seconds == 0:
        return "0m 0s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    if pd.isna(bytes_value) or bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_call_type_name(call_type):
    """Convert call type number to readable name with icons"""
    call_types = {
        1: "📞 Incoming",
        2: "📤 Outgoing", 
        3: "📵 Missed",
        4: "📧 Voicemail",
        5: "🚫 Rejected",
        6: "⛔ Blocked"
    }
    return call_types.get(call_type, f"❓ Unknown ({call_type})")

def get_message_type_name(msg_type):
    """Convert message type number to readable name with icons"""
    message_types = {
        1: "📥 Received",
        2: "📤 Sent",
        3: "📝 Draft", 
        4: "📤 Outbox",
        5: "❌ Failed",
        6: "⏳ Queued"
    }
    return message_types.get(msg_type, f"❓ Unknown ({msg_type})")

def get_app_category_icon(app_name):
    """Get category icon for app based on name"""
    app_name_lower = app_name.lower()
    
    if any(social in app_name_lower for social in ['whatsapp', 'facebook', 'instagram', 'twitter', 'telegram', 'snapchat']):
        return "💬"
    elif any(game in app_name_lower for game in ['game', 'play', 'puzzle', 'casino']):
        return "🎮"
    elif any(media in app_name_lower for media in ['youtube', 'netflix', 'spotify', 'music', 'video']):
        return "🎵"
    elif any(work in app_name_lower for work in ['office', 'word', 'excel', 'powerpoint', 'teams', 'slack']):
        return "💼"
    elif any(browser in app_name_lower for browser in ['chrome', 'firefox', 'browser', 'edge']):
        return "🌐"
    elif any(shopping in app_name_lower for shopping in ['amazon', 'flipkart', 'shopping', 'store']):
        return "🛒"
    elif any(travel in app_name_lower for travel in ['maps', 'uber', 'ola', 'travel']):
        return "🗺️"
    elif any(finance in app_name_lower for finance in ['bank', 'pay', 'wallet', 'finance']):
        return "💳"
    else:
        return "📱"

def get_user_location_info():
    """Get user's location information"""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": data.get("ip", "Unknown"),
                "city": data.get("city", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "location": f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
            }
    except:
        pass
    
    return {
        "ip": "Unknown",
        "city": "Unknown", 
        "country": "Unknown",
        "location": "Unknown"
    }