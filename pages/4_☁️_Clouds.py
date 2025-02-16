import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from datetime import timedelta

st.set_page_config(page_title="Cloud Cover Forecast", page_icon="☁️", layout="wide")

@st.cache_data(ttl=timedelta(hours=1))
def get_weather(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["cloudcover", "temperature_2m"],
        "daily": ["sunrise", "sunset"],
        "forecast_days": 10,
        "timezone": "auto"
    }
    response = requests.get(base_url, params=params)
    return response.json() if response.status_code == 200 else None


@st.cache_data(ttl=timedelta(hours=24))
def geocode(location):
    geolocator = Nominatim(user_agent="cloud_cover_forecast_app")
    return geolocator.geocode(location)

st.title("☁️ 10-Day Cloud Cover Forecast")

# Location input
location = st.text_input("Enter a location:", "London, UK")

if location:
    location_info = geocode(location)
    if location_info:
        lat, lon = location_info.latitude, location_info.longitude
        st.success(f"Showing forecast for {location_info.address}")

        weather_data = get_weather(lat, lon)
        sun_df = pd.DataFrame({
            'Date': pd.to_datetime(weather_data['daily']['time']),
            'Sunrise': pd.to_datetime(weather_data['daily']['sunrise']),
            'Sunset': pd.to_datetime(weather_data['daily']['sunset'])
        })
        if weather_data:
            df = pd.DataFrame({
                'Time': pd.to_datetime(weather_data['hourly']['time']),
                'Cloud Cover (%)': weather_data['hourly']['cloudcover'],
                'Temperature (°C)': weather_data['hourly']['temperature_2m']
            })

            # Get the current date and time
            now = pd.Timestamp.now().floor('H')

            # Filter data for the next 10 days starting from now
            df = df[(df['Time'] >= now) & (df['Time'] < now + pd.Timedelta(days=10))]

            # Add columns for date and hour
            df['Date'] = df['Time'].dt.date
            df['Hour'] = df['Time'].dt.hour

            # st.write("DataFrame head:")
            # st.write(df.head())
            # st.write("DataFrame shape:", df.shape)

            pivoted_data = df.pivot(index='Date', columns='Hour', values='Cloud Cover (%)')
            # st.write("Pivoted data head:")
            # st.write(pivoted_data.head())
            # st.write("Pivoted data shape:", pivoted_data.shape)

            # Create heatmap with reversed color scale
            fig_heatmap = px.imshow(pivoted_data,
                                    labels=dict(x="Hour of Day", y="Date", color="Cloud Cover (%)"),
                                    color_continuous_scale=["#007FFF", "#FFFFFF"],  # Blue to White
                                    title="Cloud Cover Heatmap")

            # Add sunrise and sunset vertical lines
            for _, row in sun_df.iterrows():
                sunrise_hour = row['Sunrise'].hour + row['Sunrise'].minute / 60
                sunset_hour = row['Sunset'].hour + row['Sunset'].minute / 60
                
                fig_heatmap.add_vline(x=sunrise_hour, line_width=2, line_dash="dash", line_color="orange")
                fig_heatmap.add_vline(x=sunset_hour, line_width=2, line_dash="dash", line_color="red")

            fig_heatmap.update_layout(
                height=400,
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(24)),
                    ticktext=[f"{h:02d}:00" for h in range(24)]
                ),
                yaxis=dict(
                    autorange="reversed"
                ),
                coloraxis_colorbar=dict(
                    title="Cloud Cover (%)",
                    tickvals=[0, 50, 100],
                    ticktext=["0% (Clear)", "50%", "100% (Cloudy)"]
                )
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)


            # Create line chart
            fig_line = px.line(df, x='Time', y='Cloud Cover (%)', 
                            title="Cloud Cover Forecast",
                            labels={"Cloud Cover (%)": "Cloud Cover (%)", "Time": "Date and Time"})
            fig_line.update_traces(line=dict(color="royalblue"))

            # Add clear sky markers
            fig_line.add_scatter(x=df[df['Cloud Cover (%)'] == 0]['Time'], 
                                y=df[df['Cloud Cover (%)'] == 0]['Cloud Cover (%)'],
                                mode='markers',
                                marker=dict(color="gold", size=10, symbol="star"),
                                name="Clear Sky")

            # Add sunrise markers
            fig_line.add_scatter(x=sun_df['Sunrise'], y=[0]*len(sun_df),
                                mode='markers',
                                marker=dict(color="orange", size=10, symbol="triangle-up"),
                                name="Sunrise")

            # Add sunset markers
            fig_line.add_scatter(x=sun_df['Sunset'], y=[0]*len(sun_df),
                                mode='markers',
                                marker=dict(color="red", size=10, symbol="triangle-down"),
                                name="Sunset")

            fig_line.update_layout(height=400)
            st.plotly_chart(fig_line, use_container_width=True)

            # Display hours with no cloud cover
            clear_sky = df[df['Cloud Cover (%)'] == 0]
            if not clear_sky.empty:
                st.subheader("🌞 Hours with Clear Sky (0% Cloud Cover)")
                for date, group in clear_sky.groupby('Date'):
                    st.write(f"**{date}:** {', '.join(group['Time'].dt.strftime('%I %p').tolist())}")
            else:
                st.info("No hours with completely clear sky in the next 3 days.")

            # Display average cloud cover per day
            st.subheader("Average Cloud Cover per Day")
            daily_avg = df.groupby('Date')['Cloud Cover (%)'].mean().reset_index()
            for _, row in daily_avg.iterrows():
                st.metric(f"{row['Date']}", f"{row['Cloud Cover (%)']:.1f}%")

        else:
            st.error("Unable to fetch weather data. Please try again later.")
    else:
        st.error("Location not found. Please enter a valid location.")
else:
    st.warning("Please enter a location to get the cloud cover forecast.")