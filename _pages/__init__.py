# lib/pages/__init__.py
"""
Pages module for Guardian Dashboard
Contains all page implementations
"""

from .device_overview import show_device_overview
from .locations import show_locations
from .weather import show_weather
from .call_logs import show_call_logs
from .contacts import show_contacts
from .messages import show_messages
from .phone_state import show_phone_state
from .audio_recordings import show_audio_recordings
from .installed_apps import show_installed_apps
from .app_usage import show_app_usage
from .battery_status import show_battery_status
from .system_metrics import show_system_metrics
from .sensor_data import show_sensor_data

# Define all available pages with their permissions and functions
ALL_PAGES = {
    "📱 Device Overview": ("device_overview", show_device_overview),
    "🌍 Location Tracker": ("locations", show_locations),
    "🌦️ Weather Dashboard": ("weather", show_weather),
    "📞 Call Logs": ("call_logs", show_call_logs),
    "👥 Contacts": ("contacts", show_contacts),
    "💬 Messages": ("messages", show_messages),
    "📶 Phone State": ("phone_state", show_phone_state),
    "🎙️ Audio Recordings": ("audio_recordings", show_audio_recordings),
    "📱 Installed Apps": ("installed_apps", show_installed_apps),
    "📊 App Usage Analytics": ("app_usage", show_app_usage),
    "🔋 Battery Monitoring": ("battery_status", show_battery_status),
    "🖥️ System Metrics": ("system_metrics", show_system_metrics),
    "📡 Sensor Data": ("sensor_data", show_sensor_data)
}

__all__ = [
    'show_device_overview',
    'show_locations', 
    'show_weather',
    'show_call_logs',
    'show_contacts',
    'show_messages',
    'show_phone_state',
    'show_audio_recordings',
    'show_installed_apps',
    'show_app_usage',
    'show_battery_status',
    'show_system_metrics',
    'show_sensor_data',
    'ALL_PAGES'
]