import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MousePosition
import requests
import pandas as pd

# Initialize session state for markers if it doesn't exist
if 'markers' not in st.session_state:
    st.session_state.markers = []

# Function to get weather forecast using the FREE open-meteo API
def get_forecast(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&timezone=auto&forecast_days=10"
    response = requests.get(url)
    return response.json()

# Set up the page width and title etc...
st.set_page_config(page_title="Interactive Map", layout="wide")
st.title("Click map to get 10-day temperature forecast")

# Initialize the streamlit folium map centered on a default location (e.g., London, UK)
m = folium.Map(location=[51.5074, -0.1278], zoom_start=12)

# Add mouse position display on the top corner of the map
formatter = "function(num) {return L.Util.formatNum(num, 5);};"
MousePosition(
    position="topright",
    separator=" | ",
    empty_string="NaN",
    lng_first=True,
    num_digits=20,
    prefix="Coordinates:",
    lat_formatter=formatter,
    lng_formatter=formatter,
).add_to(m)

# Add a LayerControl to the map
folium.LayerControl().add_to(m)

# Add existing markers from session state
for marker in st.session_state.markers:
    folium.Marker(marker['location'], popup=marker['popup']).add_to(m)

# Display the map and capture the last click
map_data = st_folium(m, width=300, height=300)

# Display clicked location and forecast
if map_data['last_clicked']:
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']

    # Display clicked location and forecast for out of range coordinates
    if lat is not None and lon is not None:
        # Normalize latitude
        lat = ((lat + 90) % 180) - 90
        
        # Normalize longitude
        lon = ((lon + 180) % 360) - 180

        st.write(f"Clicked Location - Latitude: {lat:.5f}, Longitude: {lon:.5f}")

        # Add new marker to session state
        new_marker = {
            'location': [lat, lon],
            'popup': f"Lat: {lat:.5f}, Lon: {lon:.5f}"
        }
        st.session_state.markers.append(new_marker)

        # Get and display forecast
        forecast_data = get_forecast(lat, lon)
        
        if forecast_data and 'hourly' in forecast_data:
            hourly = forecast_data['hourly']
            df = pd.DataFrame({
                'Time': pd.to_datetime(hourly['time']),
                'Temperature (°C)': hourly['temperature_2m']
            })

            st.subheader(f"10-Day Temperature Forecast for ({lat:.5f}, {lon:.5f})")

            # Temperature chart using Streamlit's line_chart
            st.line_chart(df.set_index('Time')['Temperature (°C)'])

        else:
            st.error("Unable to fetch forecast data. Please try again.")

# Add a button to clear all markers
if st.button('Clear All Markers'):
    st.session_state.markers = []
    st.experimental_rerun()