"""
Email OTP Authentication System
"""

import streamlit as st
import smtplib
import random
import time
import re
from email.message import EmailMessage

class EmailOTPAuth:
    """Email-based OTP authentication system"""
    
    def __init__(self, config):
        self.config = config
        self.email_config = config.email_config
    
    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    def is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_otp_email(self, email: str, otp: str) -> bool:
        """Send OTP via email using SMTP"""
        try:
            if not all([
                self.email_config["server"],
                self.email_config["username"], 
                self.email_config["password"],
                self.email_config["sender"]
            ]):
                st.error("Email configuration incomplete. Check your .env file.")
                return False

            msg = EmailMessage()
            msg["Subject"] = "Guardian Dashboard - Login OTP"
            msg["From"] = self.email_config["sender"]
            msg["To"] = email
            msg.set_content(f"""
            Hello,
            
            Your OTP for Guardian Dashboard login is: {otp}
            
            This code is valid for 5 minutes only.
            
            Best regards,
            Guardian Dashboard Team
            """)

            with smtplib.SMTP(self.email_config["server"], self.email_config["port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            st.error(f"Error sending email: {str(e)}")
            return False
    
    def login(self) -> bool:
        """Main login flow with OTP authentication"""
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
        
        if st.session_state.authenticated:
            return True

        st.subheader("🔐 Email OTP Authentication")
        
        # Email input phase
        if not st.session_state.otp:
            with st.form("email_form"):
                email = st.text_input(
                    "📧 Enter your email address",
                    placeholder="your-email@example.com"
                )
                
                if st.form_submit_button("📨 Send OTP", use_container_width=True):
                    if not email:
                        st.error("Please enter your email address")
                    elif not self.is_valid_email(email):
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("Sending OTP..."):
                            otp = self.generate_otp()
                            if self.send_otp_email(email, otp):
                                st.session_state.email = email
                                st.session_state.otp = otp
                                st.session_state.otp_timestamp = time.time()
                                st.session_state.login_attempts = 0
                                st.success("✅ OTP sent! Check your inbox.")
                                st.rerun()
        
        # OTP verification phase
        else:
            # Check if OTP is expired (5 minutes)
            if time.time() - st.session_state.otp_timestamp > 300:
                st.error("⏰ OTP expired. Please request a new one.")
                st.session_state.otp = None
                st.session_state.otp_timestamp = None
                st.rerun()
                
            st.info(f"📧 OTP sent to: {st.session_state.email}")
            
            with st.form("otp_form"):
                user_otp = st.text_input(
                    "🔢 Enter 6-digit OTP",
                    max_chars=6,
                    placeholder="123456"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    verify_clicked = st.form_submit_button("🔓 Verify", use_container_width=True)
                with col2:
                    resend_clicked = st.form_submit_button("🔄 Resend", use_container_width=True)

                if verify_clicked:
                    if not user_otp:
                        st.error("Please enter the OTP")
                    elif len(user_otp) != 6 or not user_otp.isdigit():
                        st.error("OTP must be 6 digits")
                    elif user_otp == st.session_state.otp:
                        st.session_state.authenticated = True
                        st.success("🎉 Login successful!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        if st.session_state.login_attempts >= 3:
                            st.error("Too many failed attempts. Request new OTP.")
                            st.session_state.otp = None
                            st.session_state.otp_timestamp = None
                            st.session_state.login_attempts = 0
                        else:
                            remaining = 3 - st.session_state.login_attempts
                            st.error(f"Incorrect OTP. {remaining} attempts remaining.")

                if resend_clicked:
                    with st.spinner("Resending OTP..."):
                        new_otp = self.generate_otp()
                        if self.send_otp_email(st.session_state.email, new_otp):
                            st.session_state.otp = new_otp
                            st.session_state.otp_timestamp = time.time()
                            st.session_state.login_attempts = 0
                            st.success("✅ New OTP sent!")
                            st.rerun()

        return st.session_state.authenticated