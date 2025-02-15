import streamlit as st

st.set_page_config(page_title="About", page_icon="ℹ️")

st.title("About This App")
st.write("This is a weather comparison app that shows current weather and forecasts for Cesme, Xanthi, and London.")
st.write("It uses data from the Open-Meteo API and geocoding from Nominatim.")
st.write("Created with Streamlit.")