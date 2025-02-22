import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import requests

st.title("Interactive Map with Weather Forecast")

# Function to fetch 10-day forecast from Open-Meteo
def fetch_weather_forecast(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["temperature_2m_max"],
        "timezone": "auto",
    }
    response = requests.get(url, params=params)
    if response.ok:
        data = response.json()
        return data['daily']
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
map_data = st_folium(st.session_state.map, width=700, height=500, key="folium_map")

# Check if the map was clicked
if map_data.get('last_clicked') is not None:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lon = map_data['last_clicked']['lng']
    new_row = {'Latitude': [clicked_lat], 'Longitude': [clicked_lon]}
    new_row_df = pd.DataFrame(new_row)
    st.session_state['coords_df'] = pd.concat([st.session_state['coords_df'], new_row_df], ignore_index=True)
    
    # Fetch and store the weather forecast for the clicked location
    forecast_data = fetch_weather_forecast(clicked_lat, clicked_lon)
    if forecast_data:
        st.session_state['forecasts'][(clicked_lat, clicked_lon)] = forecast_data
        st.rerun()

# Plotting the forecasts
if st.session_state['forecasts']:
    df_forecasts = pd.DataFrame()
    for coords, forecast in st.session_state['forecasts'].items():
        dates = forecast['time']
        temp_max = forecast['temperature_2m_max']
        for i, date in enumerate(dates):
            df_forecasts = pd.concat([df_forecasts, pd.DataFrame({
                'Date': [date],
                'Temperature': temp_max[i],
                'Location': f"{coords[0]}, {coords[1]}"
            })], ignore_index=True)
    
    df_forecasts = df_forecasts.pivot(index='Date', columns='Location', values='Temperature')
    st.line_chart(df_forecasts)

# Display the DataFrame with all clicked coordinates
st.dataframe(st.session_state['coords_df'])