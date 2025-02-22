import streamlit as st
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

st.title("Weather Forecast App")

# Setup the Open-Meteo API client with cache and retry on error
@st.cache_resource
def setup_api_client():
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)

openmeteo = setup_api_client()

# User input for coordinates
latitude = st.number_input("Latitude", value=52.52, format="%.2f")
longitude = st.number_input("Longitude", value=13.41, format="%.2f")

if st.button("Get Weather Forecast"):
    # API request
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location
    response = responses[0]
    st.write(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    st.write(f"Elevation: {response.Elevation()} m asl")
    st.write(f"Timezone: {response.Timezone()} {response.TimezoneAbbreviation()}")
    st.write(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()} s")

    # Process hourly data
    hourly = response.Hourly()
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "rain": hourly.Variables(2).ValuesAsNumpy()
    }

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    # st.dataframe(hourly_dataframe)

    # Create line charts
    st.line_chart(hourly_dataframe.set_index('date')[['temperature_2m', 'relative_humidity_2m']])
    st.line_chart(hourly_dataframe.set_index('date')['rain'])