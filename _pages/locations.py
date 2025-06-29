# lib/pages/locations.py
"""
Location tracking page implementation
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def show_locations(role_manager, selected_user, selected_device):
    """Enhanced location tracking with weather integration"""
    if not role_manager.can_access_feature(st.session_state.email, "locations"):
        st.error("🚫 Access Denied: You don't have permission to view locations")
        return
    
    if not role_manager.can_see_user_data(st.session_state.email, selected_user):
        st.error("🚫 Access Denied: You cannot view this user's location data")
        return
    
    st.subheader(f"🌍 Enhanced Location Tracker - {selected_user}")

    try:
        user_email = role_manager.sanitize_email(selected_user)

        # Enhanced date and time filters
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_date = st.date_input("📅 Select Date", value=datetime.now().date())
        with col2:
            hour_range = st.select_slider(
                "🕐 Select Hour Range", 
                options=list(range(24)), 
                value=(0, 23),
                format_func=lambda x: f"{x:02d}:00"
            )
        with col3:
            accuracy_filter = st.selectbox("🎯 Accuracy Filter", ["All", "High (≤10m)", "Medium (≤50m)", "Low (>50m)"])

        loc_ref = role_manager.db.collection("users").document(user_email).collection("devices").document(selected_device).collection("locations")
        
        # Filter by date and hour
        start_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour_range[0]))
        end_time = datetime.combine(selected_date, datetime.min.time().replace(hour=hour_range[1], minute=59, second=59))
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        locs = loc_ref.where("timestamp", ">=", start_timestamp).where("timestamp", "<=", end_timestamp).limit(1000).stream()

        location_data = []
        for loc in locs:
            entry = loc.to_dict()
            if "latitude" in entry and "longitude" in entry:
                entry["timestamp"] = datetime.fromtimestamp(entry.get("timestamp", 0) / 1000.0)
                location_data.append(entry)

        if not location_data:
            st.info(f"📍 No location data found for {selected_date} between {hour_range[0]:02d}:00 and {hour_range[1]:02d}:00")
            return

        df = pd.DataFrame(location_data)
        df = df.sort_values("timestamp")

        # Apply accuracy filter
        if accuracy_filter != "All":
            if accuracy_filter == "High (≤10m)":
                df = df[df.get("accuracy", float('inf')) <= 10]
            elif accuracy_filter == "Medium (≤50m)":
                df = df[df.get("accuracy", float('inf')) <= 50]
            elif accuracy_filter == "Low (>50m)":
                df = df[df.get("accuracy", float('inf')) > 50]

        if df.empty:
            st.info("📍 No location data matches your filters")
            return

        # Enhanced statistics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📍 Total Locations", len(df))
        with col2:
            st.metric("⏰ First Record", df["timestamp"].min().strftime("%H:%M:%S"))
        with col3:
            st.metric("⏰ Last Record", df["timestamp"].max().strftime("%H:%M:%S"))
        with col4:
            duration = df["timestamp"].max() - df["timestamp"].min()
            st.metric("⌛ Duration", f"{duration.total_seconds()/3600:.1f}h")
        with col5:
            if "accuracy" in df.columns:
                avg_accuracy = df["accuracy"].mean()
                st.metric("🎯 Avg Accuracy", f"{avg_accuracy:.1f}m")

        # Enhanced map visualization
        st.markdown("### 🗺️ Location Path")
        
        if len(df) > 1:
            fig = go.Figure()
            
            # Add path as lines
            fig.add_trace(go.Scattermapbox(
                mode="markers+lines",
                lon=df['longitude'],
                lat=df['latitude'],
                marker={'size': 8, 'color': 'red'},
                line={'width': 3, 'color': 'blue'},
                text=df['timestamp'].dt.strftime('%H:%M:%S'),
                name="Location Path"
            ))
            
            # Add start and end points
            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=[df.iloc[0]['longitude']],
                lat=[df.iloc[0]['latitude']],
                marker={'size': 15, 'color': 'green'},
                text="Start",
                name="Start Point"
            ))
            
            fig.add_trace(go.Scattermapbox(
                mode="markers",
                lon=[df.iloc[-1]['longitude']],
                lat=[df.iloc[-1]['latitude']],
                marker={'size': 15, 'color': 'red'},
                text="End",
                name="End Point"
            ))
            
            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(
                    center=dict(
                        lat=df['latitude'].mean(),
                        lon=df['longitude'].mean()
                    ),
                    zoom=13
                ),
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Single point map
            map_data = df[["latitude", "longitude"]].copy()
            map_data.columns = ["lat", "lon"]
            st.map(map_data, use_container_width=True)

        # Recent locations table
        with st.expander("📋 Location Records"):
            display_df = df[["timestamp", "latitude", "longitude"]].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%H:%M:%S")
            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading location data: {str(e)}")