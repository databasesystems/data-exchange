import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from datetime import timedelta

st.set_page_config(
    page_title="Weather Comparison",
    page_icon="🌤️",
    layout="wide",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# This is a weather comparison app. Version 1.0"
    }
)

# Functions
@st.cache_data(ttl=timedelta(hours=1))
def get_weather(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "hourly": ["temperature_2m", "relativehumidity_2m", "cloudcover"],
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

# Main content
st.title("Weather Comparison for Selected Locations")

locations = ["Cesme Turkey", "Xanthi Greece", "London UK", "Cairo Egypt"]

# Current Weather Section
st.header("Current Weather")
cols = st.columns(len(locations))

all_temp_data = []
all_humidity_data = []
all_cloud_data = []

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
                    
                    # Store forecast data for combined graphs
                    hourly_data = weather_data['hourly']
                    df = pd.DataFrame({
                        'Time': pd.to_datetime(hourly_data['time']),
                        'Temperature (°C)': hourly_data['temperature_2m'],
                        'Humidity (%)': hourly_data['relativehumidity_2m'],
                        'Cloud Cover (%)': hourly_data['cloudcover'],
                        'Location': location
                    })
                    all_temp_data.append(df[['Time', 'Temperature (°C)', 'Location']])
                    all_humidity_data.append(df[['Time', 'Humidity (%)', 'Location']])
                    all_cloud_data.append(df[['Time', 'Cloud Cover (%)', 'Location']])
                else:
                    st.error(f"Error fetching weather data: {weather_data}")
            else:
                st.error(f"Location not found: {location}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Forecast Graph Section
st.header("10-Day Weather Forecast Comparison")

if all_temp_data and all_humidity_data and all_cloud_data:
    combined_temp_df = pd.concat(all_temp_data, ignore_index=True)
    combined_humidity_df = pd.concat(all_humidity_data, ignore_index=True)
    combined_cloud_df = pd.concat(all_cloud_data, ignore_index=True)
    
    # Add day of week to the Time column
    combined_temp_df['Day'] = combined_temp_df['Time'].dt.strftime('%a %d %b')
    
    # Temperature Graph
    fig_temp = px.line(combined_temp_df, x='Time', y='Temperature (°C)', color='Location',
                  title='Temperature Forecast Comparison')
    fig_temp.update_layout(height=500, legend_title_text='Location')
    fig_temp.update_xaxes(
        title_text='Date',
        tickmode='array',
        tickvals=combined_temp_df['Time'][::24],  # Show tick for each day
        ticktext=combined_temp_df['Day'][::24],   # Use day of week as tick label
        tickangle=45
    )
    fig_temp.update_yaxes(title_text='Temperature (°C)')
    st.plotly_chart(fig_temp, use_container_width=True)

    # Humidity Graph
    fig_humidity = px.line(combined_humidity_df, x='Time', y='Humidity (%)', color='Location',
                  title='Humidity Forecast Comparison')
    fig_humidity.update_layout(height=500, legend_title_text='Location')
    fig_humidity.update_xaxes(
        title_text='Date',
        tickmode='array',
        tickvals=combined_humidity_df['Time'][::24],
        ticktext=combined_humidity_df['Time'][::24].dt.strftime('%a %d %b'),
        tickangle=45
    )
    fig_humidity.update_yaxes(title_text='Humidity (%)')
    st.plotly_chart(fig_humidity, use_container_width=True)

    # Cloud Cover Graph
    fig_cloud = px.line(combined_cloud_df, x='Time', y='Cloud Cover (%)', color='Location',
                  title='Cloud Cover Forecast Comparison')
    fig_cloud.update_layout(height=500, legend_title_text='Location')
    fig_cloud.update_xaxes(
        title_text='Date',
        tickmode='array',
        tickvals=combined_cloud_df['Time'][::24],
        ticktext=combined_cloud_df['Time'][::24].dt.strftime('%a %d %b'),
        tickangle=45
    )
    fig_cloud.update_yaxes(title_text='Cloud Cover (%)')
    st.plotly_chart(fig_cloud, use_container_width=True)

    for day in combined_temp_df['Time'][::24]:
        fig_temp.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightblue")
        fig_humidity.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightblue")
        fig_cloud.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightblue")

else:
    st.error("No data available for comparison.")

# Additional Information
st.info("Data is updated hourly. Last update: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
st.write("Data source: Open-Meteo API")