import streamlit as st

st.set_page_config(
    page_title="10-Day Weather Forecast",
    page_icon="ℹ️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("About the Weather Comparison App")

st.markdown("""
This Weather Comparison App is a demonstration project that showcases the capabilities of Streamlit and the Open-Meteo API for weather forecasting.

## Key Features
- Compare weather forecasts for multiple locations
- View temperature, humidity, and cloud cover predictions
- 10-day forecast visualization

## Technology Stack
- **Frontend & Backend**: [Streamlit](https://streamlit.io/)
- **Weather Data**: [Open-Meteo API](https://open-meteo.com/)

## Hosting
This app is hosted on [Streamlit Cloud](https://streamlit.io/cloud), demonstrating the ease of deploying data apps with Streamlit.

## Developer Information
This app was developed by [Database Systems](https://databasesystems.info/), a platform dedicated to exploring and sharing knowledge about database systems and related technologies.

## Disclaimer
This is a demo application and should not be used for critical decision-making. Weather predictions are based on the Open-Meteo API.

## Links
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Open-Meteo API Documentation](https://open-meteo.com/en/docs)
- [Developer's Website](https://databasesystems.info/)

""")

st.info("© 2025 Database Systems. All rights reserved.")