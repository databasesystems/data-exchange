import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from datetime import timedelta

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

# Sidebar
st.sidebar.title("Navigation")
st.sidebar.page_link("de_streamlit_app.py", label="Home")
st.sidebar.page_link("pages/About.py", label="About")

# Main content
st.title("Weather Comparison for Selected Locations")

locations = ["Cesme Turkey", "Xanthi Greece", "London UK"]

# Current Weather Section
st.header("Current Weather")
cols = st.columns(len(locations))

all_data = []

for i, location in enumerate(locations):
    with cols[i]:
        st.subheader(location)
        try:
            location_info = geocode(location)
            if location_info:
                lat, lon = location_info.latitude, location_info.longitude
                weather_data = get_weather(lat, lon)
                
                if isinstance(weather_data, dict):
                    current_weather = weather_data['current_weather']
                    st.metric("Temperature", f"{current_weather['temperature']}°C")
                    st.metric("Wind Speed", f"{current_weather['windspeed']} km/h")
                    
                    # Store forecast data for combined graph
                    hourly_data = weather_data['hourly']
                    df = pd.DataFrame({
                        'Time': pd.to_datetime(hourly_data['time']),
                        'Temperature (°C)': hourly_data['temperature_2m'],
                        'Location': location
                    })
                    all_data.append(df)
                else:
                    st.error(f"Error fetching weather data: {weather_data}")
            else:
                st.error(f"Location not found: {location}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Forecast Graph Section
st.header("Temperature Forecast Comparison (10 days)")
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Add day of week to the Time column
    combined_df['Day'] = combined_df['Time'].dt.strftime('%a %d %b')
    
    fig = px.line(combined_df, x='Time', y='Temperature (°C)', color='Location',
                  title='Temperature Forecast Comparison')
    fig.update_layout(height=500, legend_title_text='Location')
    fig.update_xaxes(
        title_text='Date',
        tickmode='array',
        tickvals=combined_df['Time'][::24],  # Show tick for each day
        ticktext=combined_df['Day'][::24],   # Use day of week as tick label
        tickangle=45
    )
    fig.update_yaxes(title_text='Temperature (°C)')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("No data available for comparison.")

for day in combined_df['Time'][::24]:
    fig.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightblue")

# Additional Information
st.info("Data is updated hourly. Last update: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))