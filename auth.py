# auth.py - Email OTP Login using SMTP in Streamlit

import streamlit as st
import smtplib
import random
import os
import time
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# Email configuration
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP via email using SMTP"""
    try:
        # Validate email configuration
        if not all([MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER]):
            st.error("❌ Email configuration incomplete. Check your .env file.")
            return False

        msg = EmailMessage()
        msg["Subject"] = "🔐 Guardian Dashboard - Login OTP"
        msg["From"] = MAIL_DEFAULT_SENDER
        msg["To"] = email
        msg.set_content(f"""
        Hello,
        
        Your OTP for Guardian Dashboard login is: {otp}
        
        This code is valid for 5 minutes only.
        
        If you didn't request this code, please ignore this email.
        
        Best regards,
        Guardian Dashboard Team
        """)

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        st.error("❌ Email authentication failed. Check your email credentials.")
        return False
    except smtplib.SMTPException as e:
        st.error(f"❌ SMTP error: {str(e)}")
        return False
    except Exception as e:
        st.error(f"❌ Error sending email: {str(e)}")
        return False

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def login() -> bool:
    """Main login flow with OTP authentication"""
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "otp" not in st.session_state:
        st.session_state.otp = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "otp_timestamp" not in st.session_state:
        st.session_state.otp_timestamp = None
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    # If already authenticated, return True
    if st.session_state.authenticated:
        return True

    # Login form
    st.subheader("🔐 Email OTP Authentication")
    
    with st.form("login_form"):
        email = st.text_input(
            "📧 Enter your email address",
            placeholder="your-email@example.com",
            help="You'll receive a 6-digit OTP code"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            send_otp_clicked = st.form_submit_button("📨 Send OTP", use_container_width=True)
        with col2:
            if st.session_state.otp:
                st.success("✅ OTP sent!")
            else:
                st.info("👆 Click to send OTP")

    # Send OTP logic
    if send_otp_clicked:
        if not email:
            st.error("❌ Please enter your email address")
        elif not is_valid_email(email):
            st.error("❌ Please enter a valid email address")
        else:
            with st.spinner("Sending OTP..."):
                otp = generate_otp()
                if send_otp_email(email, otp):
                    st.session_state.email = email
                    st.session_state.otp = otp
                    st.session_state.otp_timestamp = time.time()
                    st.session_state.login_attempts = 0
                    st.success("✅ OTP sent successfully! Check your inbox.")
                    st.rerun()

    # OTP verification
    if st.session_state.otp and st.session_state.email:
        # Check if OTP is expired (5 minutes)
        if time.time() - st.session_state.otp_timestamp > 300:  # 5 minutes
            st.error("⏰ OTP has expired. Please request a new one.")
            st.session_state.otp = None
            st.session_state.otp_timestamp = None
            st.rerun()
            
        st.info(f"📧 OTP sent to: {st.session_state.email}")
        
        with st.form("otp_form"):
            user_otp = st.text_input(
                "🔢 Enter 6-digit OTP",
                max_chars=6,
                placeholder="123456",
                help="Check your email for the verification code"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                verify_clicked = st.form_submit_button("🔓 Verify OTP", use_container_width=True)
            with col2:
                resend_clicked = st.form_submit_button("🔄 Resend OTP", use_container_width=True)

        # Verify OTP
        if verify_clicked:
            if not user_otp:
                st.error("❌ Please enter the OTP")
            elif len(user_otp) != 6 or not user_otp.isdigit():
                st.error("❌ OTP must be 6 digits")
            elif user_otp == st.session_state.otp:
                st.session_state.authenticated = True
                st.session_state.login_attempts = 0
                st.success("🎉 Login successful!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                if st.session_state.login_attempts >= 3:
                    st.error("❌ Too many failed attempts. Please request a new OTP.")
                    st.session_state.otp = None
                    st.session_state.otp_timestamp = None
                    st.session_state.login_attempts = 0
                else:
                    st.error(f"❌ Incorrect OTP. {3 - st.session_state.login_attempts} attempts remaining.")

        # Resend OTP
        if resend_clicked:
            with st.spinner("Resending OTP..."):
                new_otp = generate_otp()
                if send_otp_email(st.session_state.email, new_otp):
                    st.session_state.otp = new_otp
                    st.session_state.otp_timestamp = time.time()
                    st.session_state.login_attempts = 0
                    st.success("✅ New OTP sent!")
                    st.rerun()

    return st.session_state.authenticated