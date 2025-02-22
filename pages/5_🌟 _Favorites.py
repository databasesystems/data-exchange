import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from datetime import timedelta

# Page configuration
st.set_page_config(
    page_title="Weather Comparison",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    return response.json() if response.status_code == 200 else f"Error: {response.status_code}"

@st.cache_data(ttl=timedelta(hours=24))
def geocode(location):
    geolocator = Nominatim(user_agent="weather_app")
    return geolocator.geocode(location)

# Main content
st.title("🌟  Favorites of developer ")

# Location selection
locations = ["Cesme Turkey", "Xanthi Greece", "London UK", "Cairo Egypt"]
selected_locations = st.multiselect("Select locations to compare", locations, default=locations)

if not selected_locations:
    st.warning("Please select at least one location to compare.")
    st.stop()

# Fetch and process weather data
all_data = []

for location in selected_locations:
    try:
        location_info = geocode(location)
        if location_info:
            lat, lon = location_info.latitude, location_info.longitude
            weather_data = get_weather(lat, lon)
            
            if isinstance(weather_data, dict):
                hourly_data = weather_data['hourly']
                df = pd.DataFrame({
                    'Time': pd.to_datetime(hourly_data['time']),
                    'Temperature (°C)': hourly_data['temperature_2m'],
                    'Humidity (%)': hourly_data['relativehumidity_2m'],
                    'Cloud Cover (%)': hourly_data['cloudcover'],
                    'Location': location
                })
                all_data.append(df)
            else:
                st.error(f"Error fetching weather data for {location}: {weather_data}")
        else:
            st.error(f"Location not found: {location}")
    except Exception as e:
        st.error(f"An error occurred for {location}: {str(e)}")

if not all_data:
    st.error("No data available for comparison.")
    st.stop()

# Combine all data
combined_df = pd.concat(all_data, ignore_index=True)
combined_df['Day'] = combined_df['Time'].dt.strftime('%a %d %b')

# Create and display graphs
st.subheader("10-Day Weather Forecast Comparison")

# Define a color map with London as orange
color_map = {
    "London UK": "orange",
    "Cairo Egypt": "blue",
    "Xanthi Greece": "green",
    "Cesme Turkey": "red"}

# Define line styles (make London thicker)
line_styles = {
    "London UK": {"width": 2},  # Thicker line for London
    "Xanthi Greece": {"width": 1},
    "Cesme Turkey": {"width": 1},
    "Cairo Egypt": {"width": 1}
}


for metric in ['Temperature (°C)', 'Humidity (%)', 'Cloud Cover (%)']:
    fig = px.line(combined_df, x='Time', y=metric, color='Location',
                  title=f'{metric} Forecast Comparison', color_discrete_map=color_map)
    
# Customize line styles
    for i, location in enumerate(fig.data):
        location_name = location.name
        if location_name in line_styles:
            fig.data[i].line.update(line_styles[location_name])

    fig.update_layout(height=500, legend_title_text='Location')
    fig.update_xaxes(
        title_text='Date',
        tickmode='array',
        tickvals=combined_df['Time'][::24],
        ticktext=combined_df['Day'][::24],
        tickangle=45
    )
    fig.update_yaxes(title_text=metric)
    
    # Add vertical lines for each day
    for day in combined_df['Time'][::24]:
        fig.add_vline(x=day, line_width=1, line_dash="dash", line_color="lightblue")
    
    st.plotly_chart(fig, use_container_width=True)

# Current Weather Section
st.header("Current Weather")
current_weather = st.columns(len(selected_locations))

for i, location in enumerate(selected_locations):
    with current_weather[i]:
        st.subheader(location)
        current_data = combined_df[combined_df['Location'] == location].iloc[0]
        st.metric("Temperature", f"{current_data['Temperature (°C)']:.1f}°C")
        st.metric("Humidity", f"{current_data['Humidity (%)']:.1f}%")
        st.metric("Cloud Cover", f"{current_data['Cloud Cover (%)']:.1f}%")

# Additional Information
st.info(f"Data is updated hourly. Last update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.write("Data source: Open-Meteo API")