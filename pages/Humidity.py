import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from datetime import timedelta

st.set_page_config(
    page_title="10-Day Weather Forecast",
    page_icon="💧",
    layout="wide",
)

# Functions
@st.cache_data(ttl=timedelta(hours=1))
def get_weather(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relativehumidity_2m", "windspeed_10m", "cloudcover"],
        "forecast_days": 10
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"

@st.cache_data(ttl=timedelta(hours=24))
def geocode(location):
    geolocator = Nominatim(user_agent="weather_forecast_app")
    return geolocator.geocode(location)

# Main content
st.title("10-Day Weather Forecast")

# Location input
location = st.text_input("Enter a location:", "London, UK")

if location:
    location_info = geocode(location)
    if location_info:
        lat, lon = location_info.latitude, location_info.longitude
        st.success(f"Showing forecast for {location_info.address}")
        
        weather_data = get_weather(lat, lon)
        
        if isinstance(weather_data, dict):
            hourly_data = weather_data['hourly']
            df = pd.DataFrame({
                'Time': pd.to_datetime(hourly_data['time']),
                'Temperature (°C)': hourly_data['temperature_2m'],
                'Humidity (%)': hourly_data['relativehumidity_2m'],
                'Wind Speed (km/h)': hourly_data['windspeed_10m'],
                'Cloud Cover (%)': hourly_data['cloudcover']
            })
            
            # Daily aggregation
            df['Date'] = df['Time'].dt.date
            daily_data = df.groupby('Date').agg({
                'Temperature (°C)': ['mean', 'min', 'max'],
                'Humidity (%)': 'mean',
                'Wind Speed (km/h)': 'mean',
                'Cloud Cover (%)': 'mean'
            }).reset_index()
            
            daily_data.columns = ['Date', 'Temp_Mean', 'Temp_Min', 'Temp_Max', 'Humidity', 'Wind_Speed', 'Cloud_Cover']
            
            # Display daily forecast
            st.header("Daily Forecast")
            for _, row in daily_data.iterrows():
                date = row['Date'].strftime("%A, %B %d")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(f"{date}", f"{row['Temp_Mean']:.1f}°C", f"{row['Temp_Min']:.1f}°C to {row['Temp_Max']:.1f}°C")
                with col2:
                    st.metric("Humidity", f"{row['Humidity']:.1f}%")
                with col3:
                    st.metric("Wind Speed", f"{row['Wind_Speed']:.1f} km/h")
                with col4:
                    st.metric("Cloud Cover", f"{row['Cloud_Cover']:.1f}%")
                st.divider()
            
            # Plotting
            st.header("Weather Parameters Over Time")
            
            fig_temp = px.line(df, x='Time', y='Temperature (°C)', title='Temperature Forecast')
            st.plotly_chart(fig_temp, use_container_width=True)
            
            fig_humidity = px.line(df, x='Time', y='Humidity (%)', title='Humidity Forecast')
            st.plotly_chart(fig_humidity, use_container_width=True)
            
            fig_wind = px.line(df, x='Time', y='Wind Speed (km/h)', title='Wind Speed Forecast')
            st.plotly_chart(fig_wind, use_container_width=True)
            
            fig_cloud = px.line(df, x='Time', y='Cloud Cover (%)', title='Cloud Cover Forecast')
            st.plotly_chart(fig_cloud, use_container_width=True)
            
        else:
            st.error(f"Error fetching weather data: {weather_data}")
    else:
        st.error(f"Location not found: {location}")

# Additional Information
st.info("Data is updated hourly. Last update: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
st.write("Data source: Open-Meteo API")