import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import folium
import streamlit.components.v1 as components
from datetime import timedelta
from streamlit_extras.switch_page_button import switch_page



st.set_page_config(page_title="Weather Comparison", page_icon="🌤️", layout="wide")

# Functions

@st.cache_data(ttl=timedelta(hours=1))
def get_weather(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "hourly": "temperature_2m",
        "forecast_days": 10
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"

@st.cache_data(ttl=timedelta(hours=24))
def geocode(location):
    geolocator = Nominatim(user_agent="weather_app")
    return geolocator.geocode(location)

def create_map(lat, lon, location):
    m = folium.Map(location=[lat, lon], zoom_start=10)
    folium.Marker([lat, lon], popup=location).add_to(m)
    map_html = m.get_root().render()
    return f"""
    <style>
        #map {{
            width: 100%;
            height: 200px;
            border: none;
        }}
    </style>
    {map_html}
    """

# Home page content
st.title("Weather Data for Selected Locations")
# Sidebar (repeated for consistency)
st.sidebar.title("Navigation")
st.sidebar.page_link("de_streamlit_app.py", label="Home")
st.sidebar.page_link("pages/About.py", label="About")


locations = ["Cesme Turkey", "Xanthi Greece", "London UK"]
cols = st.columns(3)

all_data = []

for i, location in enumerate(locations):
    with cols[i]:
        st.subheader(location)
        
        location_info = geocode(location)
        if location_info:
            lat, lon = location_info.latitude, location_info.longitude
            
            # Display map
            components.html(create_map(lat, lon, location), height=200)
            
            # Fetch and display weather data
            weather_data = get_weather(lat, lon)
            
            if isinstance(weather_data, dict):
                # Current weather
                current_weather = weather_data['current_weather']
                st.write("Current Weather:")
                st.write(f"Temperature: {current_weather['temperature']}°C")
                st.write(f"Windspeed: {current_weather['windspeed']} km/h")
                
                # Store forecast data for combined graph
                hourly_data = weather_data['hourly']
                df = pd.DataFrame({
                    'Time': pd.to_datetime(hourly_data['time']),
                    'Temperature (°C)': hourly_data['temperature_2m'],
                    'Location': location
                })
                all_data.append(df)
            else:
                st.error(weather_data)
        else:
            st.error(f"Location not found: {location}")

# Combine all data and create a single graph
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    
    st.subheader("Temperature Forecast Comparison (10 days)")
    fig = px.line(combined_df, x='Time', y='Temperature (°C)', color='Location',
                  title='Temperature Forecast Comparison (10 days)')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No data available for comparison.")