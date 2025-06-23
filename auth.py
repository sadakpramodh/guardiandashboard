# auth.py - Email OTP Login using SMTP in Streamlit

import streamlit as st
import smtplib
import random
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))  # Default to port 587 if not specified
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

# Generate OTP and send it via email
def send_otp_email(email: str, otp: str) -> bool:
    try:
        msg = EmailMessage()
        msg["Subject"] = "Your Login OTP"
        msg["From"] = MAIL_DEFAULT_SENDER
        msg["To"] = email
        msg.set_content(f"Your OTP is: {otp}. It is valid for 5 minutes.")

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# Generate 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Main login flow
def login():
    st.title("🔐 Email OTP Login")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "otp" not in st.session_state:
        st.session_state.otp = None
    if "email" not in st.session_state:
        st.session_state.email = None

    if not st.session_state.authenticated:
        email = st.text_input("Enter your email")
        if st.button("Send OTP"):
            otp = generate_otp()
            if send_otp_email(email, otp):
                st.session_state.email = email
                st.session_state.otp = otp
                st.success("OTP sent! Please check your inbox.")

        if st.session_state.otp:
            user_otp = st.text_input("Enter OTP")
            if st.button("Verify OTP"):
                if user_otp == st.session_state.otp:
                    st.session_state.authenticated = True
                    st.success("Login successful!")
                else:
                    st.error("Incorrect OTP")
    else:
        st.success(f"✅ Logged in as {st.session_state.email}")
        return True

    return False
