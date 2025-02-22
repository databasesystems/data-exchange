import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import requests

st.title("Interactive Map with Weather Forecast")

# Function to fetch 10-day hourly forecast from Open-Meteo
def fetch_weather_forecast(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m"],
        "timezone": "auto",
        "forecast_days": 10
    }
    response = requests.get(url, params=params)
    if response.ok:
        data = response.json()
        return data['hourly']
    else:
        return None

# Function to create and center map based on markers
def create_centered_map(df):
    if df.empty:
        return folium.Map(location=[51.5074, -0.1278], zoom_start=10)
    else:
        # Calculate the center of the markers
        center_lat = df["Latitude"].mean()
        center_lon = df["Longitude"].mean()
        
        # Create the map centered on the mean location
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
        
        # Add markers
        for _, row in df.iterrows():
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"Lat: {row['Latitude']:.4f}, Lon: {row['Longitude']:.4f}"
            ).add_to(m)
        
        # If there's more than one marker, adjust the zoom to fit all markers
        if len(df) > 1:
            sw = df[['Latitude', 'Longitude']].min().values.tolist()
            ne = df[['Latitude', 'Longitude']].max().values.tolist()
            m.fit_bounds([sw, ne])
        
        return m

# Initialize session state variables
if 'df_click_data' not in st.session_state:
    st.session_state['df_click_data'] = pd.DataFrame(columns=["Latitude", "Longitude", "Time", "Temperature"])

# Create and render the map
st.session_state.map = create_centered_map(st.session_state['df_click_data'][["Latitude", "Longitude"]].drop_duplicates())
map_data = st_folium(st.session_state.map, width=500, height=500, key="folium_map")

# # Check if the map was clicked
if map_data.get('last_clicked') is not None:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lon = map_data['last_clicked']['lng']
    map_data = st_folium(st.session_state.map, width=500, height=500, key="folium_map")

     # Fetch and store the weather forecast for the clicked location
    forecast_data = fetch_weather_forecast(clicked_lat, clicked_lon)
    if forecast_data:
        # Create a DataFrame from the forecast data
        new_data = pd.DataFrame({
            'Latitude': clicked_lat,
            'Longitude': clicked_lon,
            'Time': pd.to_datetime(forecast_data['time']),
            'Temperature': forecast_data['temperature_2m']
        })
        
        # Add the new data to df_click_data
        st.session_state['df_click_data'] = pd.concat([st.session_state['df_click_data'], new_data], ignore_index=True)
        st.rerun()  # Force a rerun to update the chart immediately

# Display a line chart with hourly temperature forecasts for all locations
if not st.session_state['df_click_data'].empty:
    st.subheader("Hourly Temperature Forecast for All Locations")
    
    # Prepare data for the chart
    chart_data = st.session_state['df_click_data'].copy()
    chart_data['location'] = chart_data.apply(lambda row: f"Lat_{row['Latitude']:.2f}_Lon_{row['Longitude']:.2f}", axis=1)
    
    # Pivot the data using Time as index
    chart_data = chart_data.pivot_table(index='Time', 
                                        columns='location', 
                                        values='Temperature', 
                                        aggfunc='first')
    
    # Display the chart
    st.line_chart(chart_data)
    st.write("Legend:")
    for location in chart_data.columns:
        st.write(f"- {location}")
        st.rerun()
else:
    st.info("Click on the map to add markers and see weather forecasts.")

# Button to clear all markers and forecasts
if st.button("Clear All Markers and Forecasts"):
    st.session_state['df_click_data'] = pd.DataFrame(columns=["Latitude", "Longitude", "Time", "Temperature"])
    st.rerun()