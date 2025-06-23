# main.py – Entry point for Streamlit dashboard

import streamlit as st
from auth import login
from firebase_admin import credentials, firestore, initialize_app, auth
import os
from dotenv import load_dotenv
from pages.device_overview import show_device_overview
from pages.call_logs import show_call_logs
from pages.contacts import show_contacts
from pages.messages import show_messages
from pages.locations import show_locations
from pages.phone_state import show_phone_state
from pages.weather import show_weather
import pyrebase

load_dotenv()

st.set_page_config(
    page_title="Realtime Dashboard",
    layout="wide",
    initial_sidebar_state="auto"
)

# Initialize Firebase once
if "firebase_initialized" not in st.session_state:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    firebase_api_key = os.getenv("FIREBASE_API_KEY")

    if not cred_path or not os.path.exists(cred_path):
        st.error("⚠️ Firebase credentials file not found. Check GOOGLE_APPLICATION_CREDENTIALS in your .env")
        st.stop()

    # Load service account key dynamically
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
    st.session_state.firebase_initialized = True

    db = firestore.client()
    st.session_state.db = db
