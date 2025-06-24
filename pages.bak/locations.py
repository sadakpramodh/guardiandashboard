# pages/locations.py

import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
from google.cloud.firestore_v1 import Client
import numpy as np

def show_locations(db: Client):
    st.subheader("🌍 Location Tracker")

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
            st.info("Make sure your Android app is registered and sending data.")
            return

        selected_device = st.selectbox("Select a Device ID", device_ids, key="location_device_select")
        if not selected_device:
            return

        # Fetch locations subcollection
        loc_ref = devices_ref.document(selected_device).collection("locations")
        locs = loc_ref.limit(1000).stream()  # Limit to prevent timeout

        location_data = []
        for loc in locs:
            entry = loc.to_dict()
            if "latitude" in entry and "longitude" in entry:
                entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
                location_data.append(entry)

        if not location_data:
            st.info("📍 No location data found for this device.")
            st.info("Location data will appear here once the device starts tracking.")
            return

        df = pd.DataFrame(location_data)
        df = df.sort_values("timestamp")

        # Display location statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Total Locations", len(df))
        with col2:
            st.metric("📅 First Record", df["timestamp"].min().strftime("%Y-%m-%d"))
        with col3:
            st.metric("⏰ Last Record", df["timestamp"].max().strftime("%Y-%m-%d"))
        with col4:
            st.metric("🗓️ Days Tracked", (df["timestamp"].max() - df["timestamp"].min()).days)

        # Map visualization
        st.markdown("### 🗺️ Location Map")
        
        # Create map data
        map_data = df[["latitude", "longitude"]].copy()
        map_data.columns = ["lat", "lon"]
        
        # Display map
        st.map(map_data, use_container_width=True)

        # Location timeline
        st.markdown("### 📈 Movement Analysis")
        
        # Calculate movement speed (simplified approximation)
        if len(df) > 1:
            df = df.sort_values("timestamp").reset_index(drop=True)
            df["time_diff"] = df["timestamp"].diff().dt.total_seconds().fillna(0)
            
            # Calculate distance using haversine approximation (rough estimate)
            df["lat_diff"] = df["latitude"].diff().fillna(0)
            df["lon_diff"] = df["longitude"].diff().fillna(0)
            df["distance_km"] = np.sqrt(df["lat_diff"]**2 + df["lon_diff"]**2) * 111  # rough km conversion
            
            # Speed calculation (avoid division by zero)
            df["speed_kmh"] = np.where(df["time_diff"] > 0, 
                                     (df["distance_km"] / df["time_diff"]) * 3600, 
                                     0)
            
            # Filter out unrealistic speeds (>200 km/h likely GPS errors)
            df["speed_kmh"] = np.where(df["speed_kmh"] > 200, 0, df["speed_kmh"])
            
            # Show speed chart
            speed_data = df.set_index("timestamp")["speed_kmh"].fillna(0)
            if not speed_data.empty:
                st.line_chart(speed_data, use_container_width=True)
                st.caption("📊 Estimated movement speed (km/h) over time")
                
                # Speed statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🚗 Max Speed", f"{speed_data.max():.1f} km/h")
                with col2:
                    st.metric("🚶 Avg Speed", f"{speed_data.mean():.1f} km/h")
                with col3:
                    st.metric("📏 Total Distance", f"{df['distance_km'].sum():.1f} km")

        # Recent locations table
        with st.expander("📋 Recent Location Records"):
            recent_df = df.tail(20)[["timestamp", "latitude", "longitude", "deviceId"]].copy()
            st.dataframe(recent_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading location data: {str(e)}")
        st.info("Check your Firebase connection and data structure.")