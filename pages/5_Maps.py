import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import requests
from datetime import datetime, timedelta

st.title("Interactive Map with Weather Forecast")

# Function to fetch 10-day hourly forecast from Open-Meteo
def fetch_weather_forecast(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "precipitation_probability", "weathercode"],
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
        map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
        map = folium.Map(location=map_center, zoom_start=10)
        for _, row in df.iterrows():
            folium.Marker(location=[row["Latitude"], row["Longitude"]]).add_to(map)
        map.fit_bounds(map.get_bounds())
        return map

if 'coords_df' not in st.session_state:
    st.session_state['coords_df'] = pd.DataFrame(columns=["Latitude", "Longitude"])
if 'forecasts' not in st.session_state:
    st.session_state['forecasts'] = {}

# Create and render the map
st.session_state.map = create_centered_map(st.session_state['coords_df'])
map_data = st_folium(st.session_state.map, width=700, height=300, key="folium_map")

# Check if the map was clicked
if map_data.get('last_clicked') is not None:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lon = map_data['last_clicked']['lng']
    
    # Fetch and store the weather forecast for the clicked location
    forecast_data = fetch_weather_forecast(clicked_lat, clicked_lon)
    if forecast_data:
        # Create a DataFrame from the forecast data
        forecast_df = pd.DataFrame({
            'time': pd.to_datetime(forecast_data['time']),
            'temperature': forecast_data['temperature_2m'],
            'precipitation_probability': forecast_data['precipitation_probability'],
            'weathercode': forecast_data['weathercode']
        })
        
        # Add the new row to coords_df and store forecast separately
        new_row = pd.DataFrame({
            'Latitude': [clicked_lat],
            'Longitude': [clicked_lon],
        })
        st.session_state['coords_df'] = pd.concat([st.session_state['coords_df'], new_row], ignore_index=True)
        st.session_state['forecasts'][f"{clicked_lat},{clicked_lon}"] = forecast_df
        st.rerun()

# Optional: Add a button to clear all markers and the DataFrame
if st.button("Clear All Markers and Log"):
    st.session_state['coords_df'] = pd.DataFrame(columns=["Latitude", "Longitude"])
    st.session_state['forecasts'] = {}
    st.rerun()

# Display the DataFrame with all clicked coordinates
st.dataframe(st.session_state['coords_df'])

# # Display a sample of the forecast data for each location
# if not st.session_state['coords_df'].empty:
#     st.subheader("Forecast Data Samples")
#     for _, row in st.session_state['coords_df'].iterrows():
#         location_key = f"{row['Latitude']},{row['Longitude']}"
#         if location_key in st.session_state['forecasts']:
#             st.write(f"Location: Latitude {row['Latitude']:.4f}, Longitude {row['Longitude']:.4f}")
#             st.write(st.session_state['forecasts'][location_key].head())
#             st.write("---")

import pandas as pd

# Display a line chart with hourly temperature forecasts for all locations
if st.session_state['forecasts']:
    st.subheader("Hourly Temperature Forecast for All Locations")
    
    # Prepare data for the chart
    all_data = []
    for location_key, forecast_df in st.session_state['forecasts'].items():
        # Split the location_key into lat and lon
        lat, lon = map(float, location_key.split(','))
        location_name = f"Lat_{lat:.2f}_Lon_{lon:.2f}"
        
        # Ensure forecast_df has 'time' and 'temperature' columns
        if 'time' in forecast_df.columns and 'temperature' in forecast_df.columns:
            temp_df = forecast_df[['time', 'temperature']].copy()
            temp_df['location'] = location_name
            all_data.append(temp_df)
        else:
            st.warning(f"Forecast data for {location_name} is not in the expected format.")
    
    # Combine all data into a single DataFrame
    if all_data:
        chart_data = pd.concat(all_data, ignore_index=True)
        chart_data['time'] = pd.to_datetime(chart_data['time'])
        
        # Create and display the line chart
        st.line_chart(chart_data.set_index('time').pivot(columns='location', values='temperature'))

        # Optional: Add a legend
        st.write("Legend:")
        for location in chart_data['location'].unique():
            st.write(f"- {location}")
    else:
        st.warning("No valid forecast data available to display.")