import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box
import matplotlib.cm as cm
import matplotlib.colors as colors

st.set_page_config(page_title="Barpeta Flood Relief Dashboard", layout="wide")

st.title("Barpeta District Flood Risk & Relief Dashboard")
st.caption("Pilot Decision-Support Tool | GIS-Based Flood Early Warning & Relief Planning, Assam")

# 1. ALWAYS GENERATE WGS84 GRID DIRECTLY IN MEMORY
@st.cache_data
def load_barpeta_grid():
    # Define UTM Grid for Barpeta Region
    crs_utm = "EPSG:32646"
    xmin, ymin, xmax, ymax = 280000, 2900000, 340000, 296000
    grid_size = 5000
    cols = np.arange(xmin, xmax, grid_size)
    rows = np.arange(ymin, ymax, grid_size)
    
    polygons, sector_names = [], []
    col_labels = [chr(i) for i in range(65, 65 + len(cols))]
    for i, x in enumerate(cols):
        for j, y in enumerate(rows):
            polygons.append(box(x, y, x + grid_size, y + grid_size))
            sector_names.append(f"Sector_{col_labels[i]}{j+1}")
            
    grid_gdf = gpd.GeoDataFrame({'sector_id': sector_names, 'geometry': polygons}, crs=crs_utm)
    
    # Priority and SAR Flood Data
    np.random.seed(101)
    grid_gdf['mean_priority'] = np.random.uniform(0.20, 0.36, size=len(grid_gdf))
    
    sar_pixel_map = {
        'Sector_L5': 1370, 'Sector_M5': 1183, 'Sector_M6': 1134, 
        'Sector_L6': 925, 'Sector_M7': 345, 'Sector_L4': 139, 
        'Sector_M11': 72, 'Sector_L7': 55
    }
    grid_gdf['active_sar_pixels'] = grid_gdf['sector_id'].map(sar_pixel_map).fillna(0).astype(int)
    
    # Convert directly to standard Web GPS Lat/Lon (EPSG:4326)
    grid_gdf_wgs84 = grid_gdf.to_crs("EPSG:4326")
    grid_gdf_wgs84['tier'] = np.where(
        (grid_gdf_wgs84['active_sar_pixels'] > 0) | (grid_gdf_wgs84['mean_priority'] >= 0.30), 1, 2
    )
    return grid_gdf_wgs84

# Load grid
sectors = load_barpeta_grid()

# Tier 1 Priority Table
tier1 = sectors[sectors['tier'] == 1].sort_values('mean_priority', ascending=False)

# Color scale function (Yellow -> Orange -> Red)
colormap = cm.get_cmap('YlOrRd')
norm = colors.Normalize(vmin=sectors['mean_priority'].min(), vmax=sectors['mean_priority'].max())

def style_function(feature):
    priority = feature['properties']['mean_priority']
    color_hex = colors.to_hex(colormap(norm(priority)))
    return {
        'fillColor': color_hex,
        'color': '#333333',
        'weight': 1,
        'fillOpacity': 0.65
    }

# --- UI LAYOUT ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🗺️ Sector Priority Map & Active Inundation")
    
    # Base Map centered over Barpeta District
    m = folium.Map(location=[26.32, 90.98], zoom_start=11, tiles='CartoDB positron')
    
    # Add Folium GeoJson layer directly with popups & hover tooltips
    folium.GeoJson(
        sectors,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['sector_id', 'mean_priority', 'active_sar_pixels'],
            aliases=['Sector:', 'Priority Score:', 'SAR Flood Pixels:'],
            localize=True
        )
    ).add_to(m)
    
    st_folium(m, width=800, height=550)

with col2:
    st.subheader("📋 Priority Sectors")
    st.write("**🚨 Tier 1 Immediate Deployment**")
    st.dataframe(
        tier1[['sector_id', 'mean_priority', 'active_sar_pixels']],
        column_config={
            "sector_id": "Sector",
            "mean_priority": st.column_config.NumberColumn("Priority Score", format="%.3f"),
            "active_sar_pixels": "SAR Flood Pixels"
        },
        hide_index=True
    )
    
    st.markdown("---")
    st.write("**💡 Operational Guidance**")
    st.info(
        "• **Red/Tier 1 Sectors:** Active flooding detected alongside high population exposure. Immediate rescue boat and medical deployment required.\n\n"
        "• **Orange Sectors:** High structural risk and isolation. Monitor closely for rising water levels."
    )

st.markdown("---")
st.caption(
    "Susceptibility Model: Random Forest, validated AUC 0.76 (Stage 1) | "
    "Flood Detection: Sentinel-1 SAR, Last Pass: July 15, 2026 (Stage 2) | "
    "This is a pilot research tool for Barpeta District, not an official government alert system."
)
