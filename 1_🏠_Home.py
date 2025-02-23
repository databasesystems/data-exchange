import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from datetime import timedelta, datetime

st.set_page_config(
    page_title="⚡ Powerful weather graph using streamlit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(ttl=timedelta(hours=1))
def get_weather(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relativehumidity_2m", "windspeed_10m", "cloudcover", "rain"],
        "forecast_days": 10
    }
    response = requests.get(base_url, params=params)
    return response.json() if response.status_code == 200 else f"Error: {response.status_code}"

@st.cache_data(ttl=timedelta(hours=24))
def geocode(location):
    geolocator = Nominatim(user_agent="weather_forecast_app")
    return geolocator.geocode(location)

# Main content
st.title("⚡ Power graph")

# Location input
location = st.text_input("Enter a location:", "London, UK")

if not location:
    st.warning("Please enter a location to get the weather forecast.")
    st.stop()

location_info = geocode(location)
if not location_info:
    st.error(f"Location not found: {location}")
    st.stop()

lat, lon = location_info.latitude, location_info.longitude
st.success(f"Showing forecast for {location_info.address}")

weather_data = get_weather(lat, lon)

if not isinstance(weather_data, dict):
    st.error(f"Error fetching weather data: {weather_data}")
    st.stop()

hourly_data = weather_data['hourly']
df = pd.DataFrame({
    'Time': pd.to_datetime(hourly_data['time']),
    'Temperature (°C)': hourly_data['temperature_2m'],
    'Humidity (%)': hourly_data['relativehumidity_2m'],
    'Wind Speed (km/h)': hourly_data['windspeed_10m'],
    'Cloud Cover (%)': hourly_data['cloudcover'],
    'Rain (mm)': hourly_data['rain']
})

# Add a slider to select the number of days
num_days = st.slider("Number of days to forecast", min_value=1, max_value=10, value=3, step=1)

# Filter the dataframe based on the selected number of days
start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
end_date = start_date + timedelta(days=num_days)
df_filtered = df[(df['Time'] >= start_date) & (df['Time'] < end_date)]

# Create the combined plot
fig = go.Figure()

# Temperature
fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Temperature (°C)'], name="Temperature", line=dict(color="red")))

# Humidity
fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Humidity (%)'], name="Humidity", line=dict(color="blue")))

# Wind Speed
fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Wind Speed (km/h)'], name="Wind Speed", line=dict(color="green")))

# Cloud Cover
fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Cloud Cover (%)'], name="Cloud Cover", line=dict(color="gray")))

# Rain
fig.add_trace(go.Bar(x=df_filtered['Time'], y=df_filtered['Rain (mm)'], name="Rain", marker_color="lightblue", yaxis="y2"))

# Update layout
fig.update_layout(
    height=600,
    title_text=f"{num_days}-Day Weather Forecast",
    showlegend=True,
    yaxis=dict(
        title="Temperature (°C) / Humidity (%) / Wind Speed (km/h) / Cloud Cover (%)",
        side="left"
    ),
    yaxis2=dict(
        title="Rain (mm)",
        overlaying="y",
        side="right"
    ),
    xaxis=dict(title="Date")
)

# Add vertical lines for each day
for day in df_filtered['Time'][::24]:
    fig.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightgray")

st.plotly_chart(fig, use_container_width=True)

# Display daily forecast
st.header("📅 Daily Forecast")
daily_data = df_filtered.resample('D', on='Time').agg({
    'Temperature (°C)': ['mean', 'min', 'max'],
    'Humidity (%)': 'mean',
    'Wind Speed (km/h)': 'mean',
    'Cloud Cover (%)': 'mean',
    'Rain (mm)': 'sum'
}).reset_index()

daily_data.columns = ['Date', 'Temp_Mean', 'Temp_Min', 'Temp_Max', 'Humidity', 'Wind_Speed', 'Cloud_Cover', 'Rain']

for _, row in daily_data.iterrows():
    date = row['Date'].strftime("%A, %B %d")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(f"{date}", f"{row['Temp_Mean']:.1f}°C", f"{row['Temp_Min']:.1f}°C to {row['Temp_Max']:.1f}°C")
    with col2:
        st.metric("Humidity", f"{row['Humidity']:.1f}%")
    with col3:
        st.metric("Wind Speed", f"{row['Wind_Speed']:.1f} km/h")
    with col4:
        st.metric("Cloud Cover", f"{row['Cloud_Cover']:.1f}%")
    with col5:
        st.metric("Rain", f"{row['Rain']:.1f} mm")
    st.divider()

# Additional Information
st.info(f"Data is updated hourly. Last update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.write("Data source: <a href='https://open-meteo.com/en/docs' target='_blank'>Open-Meteo API</a>", unsafe_allow_html=True, help="Open-Meteo API")