import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd

st.title("Interactive Map with Click Markers and Dynamic Centering")

# Initialize or retrieve the coordinates DataFrame from the session state
if 'coords_df' not in st.session_state:
    st.session_state.coords_df = pd.DataFrame(columns=["Latitude", "Longitude"])

# Function to create and center map based on markers
def create_centered_map(df):
    # If there are no markers, initialize map with a default view
    if df.empty:
        return folium.Map(location=[51.5074, -0.1278], zoom_start=10)
    else:
        # Create a map centered on the mean of the latitude and longitude of the markers
        map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
        map = folium.Map(location=map_center, zoom_start=10)
        
        # Add markers for all coordinates in the DataFrame
        for _, row in df.iterrows():
            folium.Marker(location=[row["Latitude"], row["Longitude"]]).add_to(map)
        
        # Automatically adjust the map to fit the markers
        map.fit_bounds(map.get_bounds())
        
        return map

# Create and render the map
st.session_state.map = create_centered_map(st.session_state.coords_df)
map_data = st_folium(st.session_state.map, width=600, height=300, key="folium_map")

# Check if the map was clicked
if map_data.get('last_clicked') is not None:
    clicked_lat = map_data['last_clicked']['lat']
    clicked_lon = map_data['last_clicked']['lng']

    # Display clicked location and forecast for out of range coordinates
    # Funny thing is I am getting out of range coordinates when I 
    # click on the map. This If statement is to handle that case
    if clicked_lat is not None and clicked_lon is not None:
        # Normalize latitude
        clicked_lat = ((clicked_lat + 90) % 180) - 90
        
        # Normalize longitude
        clicked_lon = ((clicked_lon + 180) % 360) - 180
    
    # Append the clicked location to the DataFrame
    new_row = pd.DataFrame({'Latitude': [clicked_lat], 'Longitude': [clicked_lon]})
    st.session_state.coords_df = pd.concat([st.session_state.coords_df, new_row], ignore_index=True)
    
    # Rerun the app to refresh the map with the new marker and adjusted view
    st.rerun()

# Display the DataFrame with all clicked coordinates
st.dataframe(st.session_state.coords_df)

# Optional: Add a button to clear all markers and the DataFrame
if st.button("Clear All Markers and Log"):
    st.session_state.coords_df = pd.DataFrame(columns=["Latitude", "Longitude"])
    # Rerun the app to refresh the state and map
    st.rerun()