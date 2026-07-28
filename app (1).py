import streamlit as st
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import pandas as pd

st.set_page_config(page_title="Barpeta Flood Relief Dashboard", layout="wide")

st.title("Barpeta District Flood Risk & Relief Dashboard")
st.caption("Pilot Decision-Support Tool | GIS-Based Flood Early Warning & Relief Planning, Assam")

# Load Validated GeoJSON Output
@st.cache_data
def load_data():
    return gpd.read_file('barpeta_operational_sectors.geojson')

sectors = load_data()

# Filter Tier 1 Deployment Sectors
tier1 = sectors[sectors['tier'] == 1].sort_values('active_sar_pixels', ascending=False)

def get_color(priority, sar_pixels):
    if sar_pixels > 500:
        return '#bd0026' # Deep Red (Critical SAR Flood Zone)
    elif sar_pixels > 0:
        return '#f03b20' # High Priority Flood Zone
    elif priority >= 0.18:
        return '#fd8d3c' # Moderate Baseline Risk
    else:
        return '#fecc5c' # Baseline / Low Risk

def style_function(feature):
    priority = feature['properties']['mean_priority']
    sar_pixels = feature['properties']['active_sar_pixels']
    return {
        'fillColor': get_color(priority, sar_pixels),
        'color': '#222222',
        'weight': 0.8,
        'fillOpacity': 0.65
    }

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Sector Priority Map & Active Inundation")
    m = folium.Map(location=[26.32, 90.98], zoom_start=11, tiles='CartoDB positron')
    
    folium.GeoJson(
        sectors.__geo_interface__,
        style_function=style_function
    ).add_to(m)
    
    folium_static(m, width=800, height=550)

with col2:
    st.subheader("📋 Priority Sectors")
    st.write(f"**🚨 Tier 1 Deployment Sectors ({len(tier1)} Total)**")
    
    st.dataframe(
        tier1[['sector_id', 'mean_priority', 'active_sar_pixels']],
        column_config={
            "sector_id": "Sector ID",
            "mean_priority": st.column_config.NumberColumn("Priority Score", format="%.4f"),
            "active_sar_pixels": "SAR Flood Pixels"
        },
        hide_index=True,
        height=400
    )
    
    st.markdown("---")
    st.write("**💡 Operational Guidance**")
    st.info(
        "• **Red/Tier 1 Sectors:** Active SAR-detected flooding overlapping priority zones. Immediate rescue boat and medical relief allocation required.\n\n"
        "• **Primary Deployment:** Sectors L5, M5, M6, and L6 capture the majority of active inundation."
    )

st.markdown("---")
st.caption(
    "Susceptibility Model: Random Forest, validated AUC 0.76 (Stage 1) | "
    "Flood Detection: Sentinel-1 SAR, Last Pass: July 15, 2026 (Stage 2) | "
    "Data derived directly from Stage 3 barpeta_relief_priority.tif | "
    "Pilot research tool for Barpeta District, Assam."
)
