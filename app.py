import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import pandas as pd
from math import radians, cos, sin, sqrt, atan2
import altair as alt


# === CONFIG ===
API_KEY = ' CKK37U-FZVFS3-XL7YRW-5ILO'
MY_LAT = 19.85858
MY_LON = 25.20202
ALT = 10
DURATION = 1
ISS_ID = 25544


# === INIT STREAMLIT ===
st.set_page_config(page_title="Static ISS Tracker", layout="wide")


st.markdown("""
    <style>
    .stMetric label {
        font-size: 1.4rem !important;
        font-weight: bold;
    }
    .stMetric div {
        font-size: 1.8rem !important;
        color: #00ffcc;
    }
    .element-container:has(.stDownloadButton) button {
        background-color: #333;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1em;
    }
    .stButton>button {
        background-color: #007ACC;
        color: white;
        font-weight: bold;
        padding: 10px 20px;
        border-radius: 10px;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)


st.title("🛰️ Static ISS Tracker")
st.markdown("bility, and more. Built with Python, Streamlit, and N2YO API.")


# === STATE ===
if 'trail' not in st.session_state:
    st.session_state.trail = []
if 'full_path' not in st.session_state:
    st.session_state.full_path = []
if 'altitudes' not in st.session_state:
    st.session_state.altitudes = []
if 'timestamps' not in st.session_state:
    st.session_state.timestamps = []
if 'distances' not in st.session_state:
    st.session_state.distances = []
if 'speeds' not in st.session_state:
    st.session_state.speeds = []


# === Utility: Haversine Distance ===
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# === Fetch ISS Position ===
def get_iss_position():
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{ISS_ID}/{MY_LAT}/{MY_LON}/{ALT}/{DURATION}/?apiKey={API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    pos = response.json()['positions'][0]
    return pos['satlatitude'], pos['satlongitude'], pos['sataltitude']


# === Fetch TLE for sunlight check ===
def get_tle_status():
    tle_url = f"https://api.n2yo.com/rest/v1/satellite/tle/{ISS_ID}?apiKey={API_KEY}"
    tle_data = requests.get(tle_url).json()
    return tle_data.get('info', {}).get('satname', None)


# === Refresh Button ===
if st.button("🔁 Fetch Latest ISS Position"):
    try:
        lat, lon, altitude = get_iss_position()
        st.success(f"📍 ISS → Lat: {lat:.2f}, Lon: {lon:.2f}, Alt: {altitude:.2f} km")


        st.session_state.full_path.append((lat, lon))
        if len(st.session_state.full_path) > 150:
            st.session_state.full_path.pop(0)


        st.session_state.trail.append((lat, lon))
        if len(st.session_state.trail) > 10:
            st.session_state.trail.pop(0)


        now = datetime.now()
        st.session_state.timestamps.append(now)
        if len(st.session_state.timestamps) > 20:
            st.session_state.timestamps.pop(0)


        st.session_state.altitudes.append(altitude)
        if len(st.session_state.altitudes) > 20:
            st.session_state.altitudes.pop(0)


        dist = haversine(MY_LAT, MY_LON, lat, lon)
        st.session_state.distances.append(dist)


        speed = 0
        if len(st.session_state.full_path) >= 2:
            lat1, lon1 = st.session_state.full_path[-2]
            lat2, lon2 = st.session_state.full_path[-1]
            d = haversine(lat1, lon1, lat2, lon2)
            t1 = st.session_state.timestamps[-2]
            t2 = st.session_state.timestamps[-1]
            dt = (t2 - t1).total_seconds() / 3600
            if dt > 0:
                speed = d / dt
        st.session_state.speeds.append(speed)
        if len(st.session_state.speeds) > 20:
            st.session_state.speeds.pop(0)


        if get_tle_status():
            st.success("☀️ ISS is likely in sunlight")


    except Exception as e:
        st.error(f"❌ Error fetching ISS data: {e}")


# === DISPLAY MAP AND INFO SIDE-BY-SIDE ===
if st.session_state.trail:
    lat, lon = st.session_state.trail[-1]
    altitude = st.session_state.altitudes[-1]
    dist = st.session_state.distances[-1] if st.session_state.distances else 0
    speed = st.session_state.speeds[-1] if st.session_state.speeds else 0


    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("🗺️ ISS Map View")
        m = folium.Map(location=[lat, lon], zoom_start=3, tiles='CartoDB dark_matter')
        folium.Marker([lat, lon], popup=f"🚀 ISS\nLat: {lat:.2f}, Lon: {lon:.2f}, Alt: {altitude:.2f} km",
                      icon=folium.Icon(color="red", icon="rocket", prefix='fa')).add_to(m)
        folium.PolyLine(st.session_state.full_path, color='lightblue', weight=1.5, opacity=0.5).add_to(m)
        folium.PolyLine(st.session_state.trail, color='orange', weight=3, opacity=0.9).add_to(m)
        folium.Marker([MY_LAT, MY_LON], popup="📍 You (Mumbai)",
                      icon=folium.Icon(color="blue", icon="home", prefix='fa')).add_to(m)
        st_folium(m, width=700, height=500)


    with col2:
        st.subheader("📦 ISS Details")
        st.metric(label="📍 Latitude", value=f"{lat:.2f}")
        st.metric(label="📍 Longitude", value=f"{lon:.2f}")
        st.metric(label="📏 Distance from Mumbai", value=f"{dist:.2f} km")
        st.metric(label="🚁 Altitude", value=f"{altitude:.2f} km")
        st.metric(label="💨 Speed", value=f"{speed:.2f} km/h")


        st.markdown("\n---\n")
        st.markdown("**📂 Download ISS Trail CSV**")
        trail_df = pd.DataFrame(st.session_state.full_path, columns=['Latitude', 'Longitude'])
        st.download_button("⬇️ Download CSV", trail_df.to_csv(index=False), "iss_trail.csv", "text/csv")


    st.subheader("📊 Altitude Over Time")
    df_alt = pd.DataFrame({
        'Time': [t.strftime("%H:%M:%S") for t in st.session_state.timestamps],
        'Altitude (km)': st.session_state.altitudes
    })
    chart_alt = alt.Chart(df_alt).mark_line(color='#00ccff').encode(
        x='Time',
        y='Altitude (km)',
        tooltip=['Time', 'Altitude (km)']
    ).properties(height=300)
    st.altair_chart(chart_alt, use_container_width=True)


    st.subheader("w Speed Over Time")
    df_speed = pd.DataFrame({
        'Time': [t.strftime("%H:%M:%S") for t in st.session_state.timestamps],
        'Speed (km/h)': st.session_state.speeds
    })
    chart_speed = alt.Chart(df_speed).mark_line(color='#ff6699').encode(
        x='Time',
        y='Speed (km/h)',
        tooltip=['Time', 'Speed (km/h)']
    ).properties(height=300)
    st.altair_chart(chart_speed, use_container_width=True)


    with st.expander("🔭 Upcoming Visible Passes Over Mumbai"):
        try:
            passes_url = f"https://api.n2yo.com/rest/v1/satellite/visualpasses/{ISS_ID}/{MY_LAT}/{MY_LON}/10/5/300/&apiKey={API_KEY}"
            passes = requests.get(passes_url).json().get('passes', [])
            if not passes:
                st.write("No visible passes in the next 5 days.")
            else:
                for p in passes:
                    start = datetime.utcfromtimestamp(p['startUTC']).strftime("%Y-%m-%d %H:%M UTC")
                    duration = p['duration']
                    st.write(f" {start} for  {duration} seconds")
        except:
            st.warning("It will be visible around 5 days.")
else:
    st.info("Click '🔁 Fetch Latest ISS Position' to start tracking.")

