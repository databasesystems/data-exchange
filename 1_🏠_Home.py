import streamlit as st
import requests
import calendar
import pandas as pd
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
from datetime import timedelta, datetime, time


# Streamlit Page Setup
st.set_page_config(
    page_title="Weather Forecast",
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

def generate_weather_summary(df_filtered, num_days, location_name):
    summaries = {}
    
    # Temperature summary
    temp_summary = df_filtered.groupby(df_filtered['Time'].dt.date)['Temperature (°C)'].max()
    min_max_temp = temp_summary.min()
    max_max_temp = temp_summary.max()
    max_temp_day = temp_summary.idxmax()
    days_to_max_temp = (max_temp_day - datetime.now().date()).days
    
    if days_to_max_temp == 0:
        temp_day_phrase = "today"
    elif days_to_max_temp == 1:
        temp_day_phrase = "tomorrow"
    else:
        temp_day_phrase = f"in {days_to_max_temp} days ({max_temp_day.strftime('%A')})"
    
    summaries['temperature'] = f"Max temperature of {max_max_temp:.1f}°C expected {temp_day_phrase}. Range: {min_max_temp:.1f}°C to {max_max_temp:.1f}°C."

    # Rain summary
    rain_days = df_filtered[df_filtered['Rain (mm)'] > 0.1]
    if not rain_days.empty:
        total_rain = rain_days['Rain (mm)'].sum()
        rain_days_count = rain_days['Time'].dt.date.nunique()
        max_rain_day = rain_days.groupby(rain_days['Time'].dt.date)['Rain (mm)'].sum().idxmax()
        days_to_max_rain = (max_rain_day - datetime.now().date()).days
        
        if days_to_max_rain == 0:
            rain_day_phrase = "today"
        elif days_to_max_rain == 1:
            rain_day_phrase = "tomorrow"
        else:
            rain_day_phrase = f"in {days_to_max_rain} days ({max_rain_day.strftime('%A')})"
        
        summaries['rain'] = f"Rain expected on {rain_days_count} days, totaling {total_rain:.1f} litres per m². Heaviest rain {rain_day_phrase}."
    else:
        summaries['rain'] = "No significant rain expected."

    # Wind summary
    windy = df_filtered[df_filtered['Wind Speed (km/h)'] > 20]
    if not windy.empty:
        max_wind = windy['Wind Speed (km/h)'].max()
        max_wind_time = windy.loc[windy['Wind Speed (km/h)'].idxmax(), 'Time']
        days_until_max_wind = (max_wind_time.date() - datetime.now().date()).days
        
        time_of_day = "day" if 6 <= max_wind_time.hour < 18 else "night"
        formatted_time = max_wind_time.strftime("%I:%M %p")
        
        if days_until_max_wind == 0:
            day_phrase = f"today at {formatted_time}"
        elif days_until_max_wind == 1:
            day_phrase = f"tomorrow at {formatted_time}"
        else:
            day_name = max_wind_time.strftime("%A")
            day_phrase = f"in {days_until_max_wind} days ({day_name}) at {formatted_time}"
        
        summaries['wind'] = f"Max wind speed of {max_wind:.1f} km/h expected {day_phrase} during the {time_of_day}."
    else:
        summaries['wind'] = "No strong winds expected."

    # Cloud summary
    def is_night(dt):
        return dt.hour < 6 or dt.hour >= 18

    day_cloud_cover = df_filtered[~df_filtered['Time'].apply(is_night)]['Cloud Cover (%)']
    night_cloud_cover = df_filtered[df_filtered['Time'].apply(is_night)]['Cloud Cover (%)']

    day_avg_cloud_cover = day_cloud_cover.mean() if not day_cloud_cover.empty else 0
    night_avg_cloud_cover = night_cloud_cover.mean() if not night_cloud_cover.empty else 0

    def get_cloud_description(avg_cloud_cover):
        if avg_cloud_cover < 30:
            return "Mostly clear skies"
        elif avg_cloud_cover < 70:
            return "Partly cloudy"
        else:
            return "Mostly cloudy"

    day_description = get_cloud_description(day_avg_cloud_cover)
    night_description = get_cloud_description(night_avg_cloud_cover)

    if night_avg_cloud_cover < 30:
        clear_night_percentage = 100 - night_avg_cloud_cover
        night_description = f"Starry night! {clear_night_percentage:.0f}% clear skies"

    summaries['clouds'] = f"Day: {day_description} (Avg. {day_avg_cloud_cover:.0f}% cloud cover)\n"
    summaries['clouds'] += f"Night: {night_description} (Avg. {night_avg_cloud_cover:.0f}% cloud cover)"

    return summaries

# UI starts
st.title("⚡ Weather Forecast")

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

    # Assuming you have df_filtered, num_days, and location_name
    summaries = generate_weather_summary(df_filtered, num_days, location_info.address)


    # Add custom CSS for card styling
    st.markdown("""
    <style>
        .weather-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #e0e0e0;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .weather-card h3 {
            color: #1e88e5;
            margin-bottom: 15px;
            font-size: 1.2rem;
            font-weight: 600;
        }
        .weather-card .icon {
            font-size: 3rem;
            margin-bottom: 15px;
            text-align: center;
        }
        .weather-card p {
            font-size: 0.9rem;
            color: #333;
            margin-bottom: 0;
            line-height: 1.4;
        }
        .stColumns {
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

    def create_card(title, icon, content):
        return f"""
        <div class="weather-card">
            <h3>{title}</h3>
            <div class="icon">{icon}</div>
            <p>{content}</p>
        </div>
        """

    # Create four columns for the cards
    col1, col2, col3, col4 = st.columns(4)

    # Define the card contents
    cards = [
        ("Temperature", "🌡️", summaries['temperature']),
        ("Rain", "🌧️", summaries['rain']),
        ("Wind", "💨", summaries['wind']),
        ("Clouds", "☁️", summaries['clouds'])
    ]

    # Create cards in columns
    for col, (title, icon, content) in zip([col1, col2, col3, col4], cards):
        with col:
            st.markdown(create_card(title, icon, content), unsafe_allow_html=True)





    # Plotting
    fig = go.Figure()
    # Display the figure without the modebar
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Temperature (°C)'], name="Temperature", line=dict(color="yellow")))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Humidity (%)'], name="Humidity", visible="legendonly", line=dict(color="#4682B4")))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Wind Speed (km/h)'], name="Wind Speed", visible="legendonly", line=dict(color='#2E8B57') )) # This is the color code for a brown-yellow shade))  fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Cloud Cover (%)'], name="Cloud Cover", visible="legendonly"))
    fig.add_trace(go.Scatter(x=df_filtered['Time'], y=df_filtered['Cloud Cover (%)'], name="Cloud Cover", visible="legendonly", line=dict(color="grey")))
    fig.add_trace(go.Bar(x=df_filtered['Time'], y=df_filtered['Rain (mm)'], name="Rain", marker_color="lightblue", yaxis="y2"))

    fig.update_layout(
        title=f"{num_days}-Day Weather Forecast",
        yaxis=dict(
            title="°C / % / km/h",
            fixedrange=True,
            range=[0, max(df_filtered['Temperature (°C)'].max(), df_filtered['Humidity (%)'].max(), df_filtered['Wind Speed (km/h)'].max()) * 1.1]
        ),
        yaxis2=dict(title="Rain (mm)", overlaying="y", side="right", fixedrange=True),
        xaxis_title="Time",
        xaxis=dict(fixedrange=True),
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        ),
        dragmode=False
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
    st.caption("Click on the legend items to show/hide different weather metrics on the chart. 👆 ")

else:
    st.info("Please enter a location to see the weather forecast.")
