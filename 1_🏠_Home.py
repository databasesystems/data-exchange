import streamlit as st
import requests
import calendar
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from datetime import timedelta, datetime


# Streamlit Page Setup
st.set_page_config(
    page_title="⚡ Weather Forecast with Narration",
    page_icon="⚡",
    layout="wide"
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

# No caching here, Nominatim may return unhashable objects
def geocode(location):
    geolocator = Nominatim(user_agent="weather_forecast_app")
    return geolocator.geocode(location)

# def geocode(location):
#     try:
#         url = "https://photon.komoot.io/api/"
#         params = {"q": location, "limit": 1}
#         response = requests.get(url, params=params, timeout=5)
#         response.raise_for_status()
#         data = response.json()
#         if data["features"]:
#             feature = data["features"][0]
#             coords = feature["geometry"]["coordinates"]
#             lat = coords[1]
#             lon = coords[0]
#             address = feature["properties"].get("name", location)
#             return {"lat": lat, "lon": lon, "address": address}
#     except Exception as e:
#         print(f"Geocoding error: {e}")
#     return None


def generate_weather_summary(df_filtered, num_days, location_name):
    sentences = []
    
    # Introduction
    intro = f"Weather forecast for {location_name} for the next {num_days} days:"
    sentences.append(intro)

    # Temperature range (using only max temperatures)
    temp_summary = df_filtered.groupby(df_filtered['Time'].dt.date)['Temperature (°C)'].max()
    min_max_temp = temp_summary.min()
    max_max_temp = temp_summary.max()
    temp_sentence = f"Maximum temperatures will range between {min_max_temp:.1f}°C and {max_max_temp:.1f}°C."
    sentences.append(temp_sentence)

    # Rain forecast
    rain_days = df_filtered[df_filtered['Rain (mm)'] > 0.1]
    if not rain_days.empty:
        for day, group in rain_days.groupby(rain_days['Time'].dt.date):
            days_from_now = (day - datetime.now().date()).days
            rain_start = group['Time'].min().strftime('%H:%M')
            rain_end = group['Time'].max().strftime('%H:%M')
            total_rain = group['Rain (mm)'].sum()
            
            day_name = calendar.day_name[day.weekday()]
            if days_from_now == 0:
                day_phrase = "today"
            elif days_from_now == 1:
                day_phrase = "tomorrow"
            else:
                day_phrase = f"{days_from_now} days from now on {day_name}"
            
            rain_sentence = f"Rain is expected {day_phrase} between {rain_start} and {rain_end}, with approximately {total_rain:.1f} liters of rain per square meter."
            sentences.append(rain_sentence)
    else:
        no_rain_sentence = f"No significant rain is expected during the forecast period."
        sentences.append(no_rain_sentence)

    # Wind forecast
    windy = df_filtered[df_filtered['Wind Speed (km/h)'] > 20]
    if not windy.empty:
        max_wind = windy['Wind Speed (km/h)'].max()
        wind_day = windy['Time'].dt.date.min()
        days_to_wind = (wind_day - datetime.now().date()).days
        wind_day_name = calendar.day_name[wind_day.weekday()]
        
        if days_to_wind == 0:
            wind_day_phrase = "today"
        elif days_to_wind == 1:
            wind_day_phrase = "tomorrow"
        else:
            wind_day_phrase = f"{days_to_wind} days from now on {wind_day_name}"
        
        wind_sentence = f"Winds may reach up to {max_wind:.1f} km/h {wind_day_phrase}."
        sentences.append(wind_sentence)

    return " ".join(sentences)

# UI starts
st.title("⚡ Weather Forecast with Narration")

location = st.text_input("Enter a location", "London, UK")
if location:
    location_info = geocode(location)
    if not location_info:
        st.error("Location not found.")
        st.stop()

    lat, lon = location_info.latitude, location_info.longitude
    weather_data = get_weather(lat, lon)

    if not isinstance(weather_data, dict):
        st.error(f"Error fetching weather data: {weather_data}")
        st.stop()

    st.success(f"Forecast for: {location_info.address}")

    df = pd.DataFrame({
            'Time': pd.to_datetime(weather_data['hourly']['time']),
            'Temperature (°C)': weather_data['hourly']['temperature_2m'],
            'Humidity (%)': weather_data['hourly']['relativehumidity_2m'],
            'Wind Speed (km/h)': weather_data['hourly']['windspeed_10m'],
            'Cloud Cover (%)': weather_data['hourly']['cloudcover'],
            'Rain (mm)': weather_data['hourly']['rain']
        })

    num_days = st.slider("Days to forecast", 1, 10, 5, key="forecast_days_slider")
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=num_days)
    df_filtered = df[(df['Time'] >= start_date) & (df['Time'] < end_date)]

    summary_text = generate_weather_summary(df_filtered, num_days, location_info.address)


    st.subheader("📋 Weather Narrative")
    st.markdown(f"> {summary_text}")



    # Plotting
    fig = go.Figure()
    # Display the figure without the modebar
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Temperature (°C)'], name="Temperature", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Humidity (%)'], name="Humidity", visible="legendonly", line=dict(color="lightblue")))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Wind Speed (km/h)'], name="Wind Speed", visible="legendonly", line=dict(color='yellow') )) # This is the color code for a brown-yellow shade))  fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Cloud Cover (%)'], name="Cloud Cover", visible="legendonly"))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Cloud Cover (%)'], name="Cloud Cover", visible="legendonly", line=dict(color="blue")))
    fig.add_trace(go.Bar(x=df_filtered['Time'], y=df_filtered['Rain (mm)'], name="Rain", marker_color="lightblue", yaxis="y2"))

    fig.update_layout(
        title=f"{num_days}-Day Weather Forecast",
        yaxis=dict(title="°C / % / km/h"),
        yaxis2=dict(title="Rain (mm)", overlaying="y", side="right"),
        xaxis_title="Time",
        height=600
    )

    fig.update_layout(
    showlegend=True,
    modebar=dict(
        remove=[
            'zoom',
            'pan',
            'select',
            'zoomIn',
            'zoomOut',
            'autoScale',
            'resetScale',
            'hover',
            'lasso',
            'resetViewMapbox',
            'toImage',
            'toggleSpikelines'
        ]
    )
)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please enter a location to see the weather forecast.")
