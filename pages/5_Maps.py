import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import MousePosition
import requests
import pandas as pd

# Function to get weather forecast
def get_forecast(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m&timezone=auto&forecast_days=10"
    response = requests.get(url)
    return response.json()

# Set up the page
st.set_page_config(page_title="Interactive Map", layout="wide")
st.title("Click on the map to add a marker and get 10-day temperature forecast")

# Initialize the map centered on a default location (e.g., New York City)
m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

# Add mouse position display
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

# Display the map and capture the last click
map_data = st_folium(m, width=400, height=400)

# Display clicked location and forecast
if map_data['last_clicked']:
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    st.write(f"Clicked Location - Latitude: {lat:.5f}, Longitude: {lon:.5f}")

    # Add a marker to the map
    folium.Marker(
        [lat, lon], popup=f"Lat: {lat:.5f}, Lon: {lon:.5f}"
    ).add_to(m)

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

        # Display additional information
        st.write("Hourly temperature data for the next 10 days:")
        st.dataframe(df)
    else:
        st.error("Unable to fetch forecast data. Please try again.")