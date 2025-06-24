# pages/weather.py

import streamlit as st
import pandas as pd
from datetime import datetime
from google.cloud.firestore_v1 import Client

def show_weather(db: Client):
    st.subheader("🌦️ Weather Logs")

    # Process email for Firestore structure
    user_email = st.session_state.email.replace('.', '_dot_').replace('@', '_at_') \
        .replace('/', '_').replace('[', '_').replace(']', '_').replace('*', '_').replace('?', '_')

    try:
        # Get devices from the correct path
        devices_ref = db.collection("users").document(user_email).collection("devices")
        devices = devices_ref.stream()
        device_ids = [doc.id for doc in devices]

        if not device_ids:
            st.warning("⚠️ No devices found.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="weather_device_select")
        if not selected_device:
            return

        # Fetch weather subcollection
        weather_ref = devices_ref.document(selected_device).collection("weather")
        records = weather_ref.limit(1000).stream()

        weather_data = []
        for rec in records:
            entry = rec.to_dict()
            entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
            weather_data.append(entry)

        if not weather_data:
            st.info("🌦️ No weather data found for this device.")
            return

        df = pd.DataFrame(weather_data)
        df = df.sort_values("timestamp", ascending=False)

        # Weather statistics
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Records", len(df))
            with col2:
                if "temperature" in df.columns:
                    st.metric("🌡️ Avg Temp", f"{df['temperature'].mean():.1f}°C")
            with col3:
                if "humidity" in df.columns:
                    st.metric("💧 Avg Humidity", f"{df['humidity'].mean():.1f}%")
            with col4:
                if "city_name" in df.columns:
                    unique_cities = df["city_name"].nunique()
                    st.metric("🏙️ Cities", unique_cities)

        # Display weather data table
        st.markdown("### 🌤️ Weather Records")
        display_columns = ["timestamp", "city_name", "description", "temperature", "humidity", "wind_speed"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            st.dataframe(df[available_columns], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

        # Weather charts
        if not df.empty:
            with st.expander("📈 Weather Trends"):
                chart_data = df.set_index("timestamp")
                
                # Temperature and humidity chart
                if "temperature" in df.columns and "humidity" in df.columns:
                    chart_cols = ["temperature", "humidity"]
                    available_chart_cols = [col for col in chart_cols if col in chart_data.columns]
                    if available_chart_cols:
                        st.line_chart(chart_data[available_chart_cols])
                        st.caption("🌡️ Temperature (°C) and 💧 Humidity (%) over time")

                # Wind speed chart
                if "wind_speed" in df.columns:
                    st.line_chart(chart_data["wind_speed"])
                    st.caption("💨 Wind Speed over time")

    except Exception as e:
        st.error(f"❌ Error loading weather data: {str(e)}")
        st.info("Check your Firebase connection and data structure.")