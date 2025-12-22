"""
Tab 2: Abnormal Events Analysis - Enhanced Professional Version
Safety incidents and risk assessment across routes
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.graph_objects as go
import json
import os
from pathlib import Path
from shapely.geometry import Polygon
from branca.element import MacroElement, Template

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════════
# PROFESSIONAL COMPONENTS
# ════════════════════════════════════════════════════════════════════════════════

def create_section_header(title, description=None):
    """Create professional section headers"""
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h2 style="color: #1f2937; margin-bottom: 0.5rem; font-weight: 600;">{title}</h2>
        {f'<p style="color: #6b7280; margin: 0;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def create_abnormal_metrics(abnormal_df):
    """Create professional metrics for abnormal events analysis"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_abnormal = len(abnormal_df['street_name'].unique()) if not abnormal_df.empty else 0
    high_risk_routes = len(abnormal_df[abnormal_df['trend'] == 'Increase']) if not abnormal_df.empty else 0
    improved_routes = len(abnormal_df[abnormal_df['trend'] == 'Decrease']) if not abnormal_df.empty else 0
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Streets</div>
            <div class="kpi-value">{total_abnormal}</div>
            <div class="kpi-change">With Abnormal Events</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Increased Risk</div>
            <div class="kpi-value">{high_risk_routes}</div>
            <div class="kpi-change negative">Require Attention</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Improved Safety</div>
            <div class="kpi-value">{improved_routes}</div>
            <div class="kpi-change positive">Positive Trend</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        improvement_rate = int((improved_routes / total_abnormal * 100)) if total_abnormal > 0 else 0
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Improvement Rate</div>
            <div class="kpi-value">{improvement_rate}%</div>
            <div class="kpi-change positive">Safety Progress</div>
        </div>
        """, unsafe_allow_html=True)

def create_abnormal_detail_card(street_name, row):
    """Create professional abnormal event detail cards"""
    
    # Create the main card container
    with st.container():
        # Card header with centered road name
        st.markdown(f"""
        <div style="background: light grey; border-radius: 8px; padding: 2rem; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem;">
            <div style="text-align: center;">
                <h3 style="margin: 0 0 0rem 0; color: #1f2937; font-weight: 600; font-size: 2.5rem;">{street_name}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        trend = row.get('trend', 'No trend data available')
        safety_status = "Improved Safety" if trend == 'Decrease' else "Increased Risk"
        
        # Metrics using columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_events = row.get('total_events', 'N/A')
            if total_events != 'N/A':
                try:
                    total_events = int(float(total_events))
                except:
                    pass
            st.markdown(f"""
            <div style="text-align: center; background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; border: 1px solid #f1f5f9; min-height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.9rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;">Total Events</div>
                <div style="font-size: 2rem; font-weight: 800; color: #1e293b;">{total_events}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            peak = row.get('peak', 'N/A')
            st.markdown(f"""
            <div style="text-align: center; background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; border: 1px solid #f1f5f9; min-height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.9rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;">Peak Period</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: #1e293b; line-height: 1.2;">{peak}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            safety_color = "#10b981" if safety_status == "Improved Safety" else "#f43f5e"
            st.markdown(f"""
            <div style="text-align: center; background: #f8fafc; padding: 1.5rem; border-radius: 12px; margin: 0.5rem; border: 1px solid #f1f5f9; min-height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 0.9rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;">Safety Status</div>
                <div style="font-size: 1.75rem; font-weight: 800; color: {safety_color}; line-height: 1.2;">{safety_status}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Close the card container
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Content sections with spacing
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        
        trend_strength = row.get('Trend Strength', 'N/A')
        # Capitalize first word
        if trend_strength != 'N/A':
            trend_strength = trend_strength.capitalize()
        st.markdown(f"**Trend Strength:** {trend_strength}")
        
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("**AI Analysis**")
        ai_summary = row.get('AI Summary', 'No AI analysis available')
        # Make "Probable Cause:" bold
        ai_summary = ai_summary.replace('Probable Cause:', '**Probable Cause:**')
        st.markdown(ai_summary)

# ════════════════════════════════════════════════════════════════════════════════
# DATA LOADING FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def get_data_directory():
    """
    Dynamically determine data directory for both local and Streamlit Cloud deployment.
    Returns the correct path to the tab2_abnormaltrend directory.
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
    
    # Try multiple possible locations
    possible_paths = [
        # Relative to script (assuming script is in src/)
        script_dir.parent / "data" / "processed" / "tab2_abnormaltrend",
        # From current working directory
        Path.cwd() / "data" / "processed" / "tab2_abnormaltrend",
        # Streamlit Cloud typical structure
        Path("/mount/src") / Path.cwd().name / "data" / "processed" / "tab2_abnormaltrend",
        # Alternative Streamlit Cloud structure
        Path("/mount/src/dlr-dashboard/data/processed/tab2_abnormaltrend"),
        # Direct path if already in the right place
        Path("data/processed/tab2_abnormaltrend"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # If none exist, return the most likely path and let caller handle the error
    return script_dir.parent / "data" / "processed" / "tab2_abnormaltrend"

@st.cache_data
def load_abnormal_events_data():
    """Load preprocessed abnormal events data from CSV"""
    try:
        data_dir = get_data_directory()
        csv_path = data_dir / "dlr-abnormal-events.csv"
        
        if not csv_path.exists():
            st.error(f"CSV file not found at: {csv_path}")
            st.info(f"Looked in directory: {data_dir}")
            return pd.DataFrame()
        
        df = pd.read_csv(csv_path)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Remove the index column if it exists (the # column)
        if '#' in df.columns:
            df = df.drop(columns=['#'])
        
        # Remove rows where street_name is empty or NaN
        df = df.dropna(subset=['street_name'])
        df = df[df['street_name'].str.strip() != '']
        
        # Clean up any encoding issues in street names
        df['street_name'] = df['street_name'].str.replace('â€™', "'", regex=False)
        df['street_name'] = df['street_name'].str.replace('Ãƒ', 'á', regex=False)
        
        # Standardize street names by stripping whitespace
        df['street_name'] = df['street_name'].str.strip()
        
        return df
    
    except Exception as e:
        st.error(f"Error loading abnormal events CSV data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_abnormal_events_segments():
    """Load abnormal events segment geometry from GeoJSON file"""
    try:
        data_dir = get_data_directory()
        geojson_path = data_dir / "abnormal-events.geojson"
        
        if not geojson_path.exists():
            st.error(f"GeoJSON file not found at: {geojson_path}")
            st.info(f"Looked in directory: {data_dir}")
            return None
        
        # Load GeoJSON directly as JSON to avoid PROJ errors
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        # Extract features into a DataFrame
        features = geojson_data.get('features', [])
        
        data = []
        for feature in features:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            data.append({
                'street_name': properties.get('street_name', '').strip(),
                'geometry': geometry
            })
        
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        st.error(f"Error loading GeoJSON data: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

@st.cache_data
def load_cycleways_data():
    """Load cycleway data from GeoJSON"""
    try:
        if not GEOPANDAS_AVAILABLE:
            return pd.DataFrame()
        
        # Try to find cycleways file in parent data directory
        script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        
        possible_paths = [
            script_dir.parent / "data" / "cycleways.geojson",
            Path.cwd() / "data" / "cycleways.geojson",
            Path("/mount/src") / Path.cwd().name / "data" / "cycleways.geojson",
            Path("/mount/src/dlr-dashboard/data/cycleways.geojson"),
            Path("data/cycleways.geojson"),
        ]
        
        for path in possible_paths:
            if path.exists():
                # Read GeoJSON without CRS operations to avoid PROJ errors
                gdf = gpd.read_file(path)
                # GeoJSON is always in WGS84 by specification
                return gdf
        
        return pd.DataFrame()
    
    except Exception as e:
        return pd.DataFrame()

# ════════════════════════════════════════════════════════════════════════════════
# MAP VISUALIZATION FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def calculate_bounds_from_geometries(geometries):
    """Calculate total bounds from list of GeoJSON geometries"""
    min_lon, min_lat = float('inf'), float('inf')
    max_lon, max_lat = float('-inf'), float('-inf')
    
    for geom in geometries:
        coords = geom.get('coordinates', [[]])
        if geom.get('type') == 'Polygon':
            for ring in coords:
                for lon, lat in ring:
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
    
    if min_lon == float('inf'):  # No valid coordinates found
        return [-6.3, 53.2, -6.1, 53.4]  # Default Dublin bounds
    
    return [min_lon, min_lat, max_lon, max_lat]

def create_abnormal_events_map(abnormal_df, segments_df, show_cycleways=False):
    """Create an interactive map showing abnormal events with geometry"""
    
    if segments_df is None or segments_df.empty:
        st.warning("No segment geometry available")
        return folium.Map(location=[53.2913, -6.1360], zoom_start=13), 0
    
    # Calculate map center from segments
    bounds = calculate_bounds_from_geometries(segments_df['geometry'].tolist())
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles='CartoDB positron',
        control_scale=False
    )
    
    # Add cycleways if requested
    if show_cycleways:
        cycleways_gdf = load_cycleways_data()
        if not cycleways_gdf.empty:
            try:
                folium.GeoJson(
                    cycleways_gdf,
                    name="Cycleways",
                    style_function=lambda x: {
                        'color': '#1f77b4',
                        'weight': 2,
                        'opacity': 0.7
                    },
                    tooltip=None,
                    popup=None
                ).add_to(m)
            except:
                pass  # Skip cycleways if there's an error
    
    routes_added = 0
    
    # Add polygons for each street
    for idx, row in segments_df.iterrows():
        street_name = row['street_name']
        geometry = row['geometry']
        
        # Find corresponding data in abnormal_df
        street_data = abnormal_df[abnormal_df['street_name'] == street_name]
        
        if street_data.empty:
            continue
        
        main_row = street_data.iloc[0]
        trend = main_row.get('trend', 'Unknown')
        total_events = main_row.get('total_events', 0)
        # Convert to int to remove decimal
        try:
            total_events = int(float(total_events))
        except:
            pass
        peak = main_row.get('peak', 'N/A')
        trend_strength = main_row.get('Trend Strength', 'N/A')
        # Capitalize first word of trend strength
        if trend_strength != 'N/A':
            trend_strength = trend_strength.capitalize()
        
        # Determine color based on trend
        if trend == 'Increase':
            color = '#ef4444'  # Red
            fill_color = '#fee2e2'
            status_text = "Increased Risk"
        elif trend == 'Decrease':
            color = '#22c55e'  # Green
            fill_color = '#d1fae5'
            status_text = "Improved Safety"
        else:
            color = '#6b7280'  # Gray
            fill_color = '#f3f4f6'
            status_text = "No Change"
        
        # Create popup content - format matches original for click detection
        popup_html = f"""
        <div style="width: 350px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5;">
            <h4 style="margin: 0 0 16px 0; color: {color};
                       font-size: 18px; font-weight: 600;">
                {street_name}
            </h4>

            <div style="margin-bottom: 16px;">
                <div style="margin-bottom: 12px;">
                    <strong>Status:</strong> <span style="color: {color}; font-weight: 600;">{status_text}</span>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <strong>Total Events:</strong> {total_events}
                </div>
                
                <div style="margin-bottom: 12px;">
                    <strong>Peak Period:</strong> {peak}
                </div>
                
                <div style="margin-bottom: 12px;">
                    <strong>Trend Strength:</strong> {trend_strength}
                </div>
            </div>
        </div>
        """
        
        # Convert GeoJSON geometry to coordinates for Folium Polygon
        try:
            if geometry.get('type') == 'Polygon':
                # GeoJSON format: [[[lon, lat], [lon, lat], ...]]
                # Folium format: [[lat, lon], [lat, lon], ...]
                coords = geometry.get('coordinates', [[]])[0]  # Get outer ring
                locations = [[lat, lon] for lon, lat in coords]  # Swap lon/lat to lat/lon
                
                folium.Polygon(
                    locations=locations,
                    color=color,
                    weight=4,
                    opacity=0.9,
                    fill=True,
                    fillColor=fill_color,
                    fillOpacity=0.5,
                    line_cap='round',
                    line_join='round',
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=street_name
                ).add_to(m)
                
                routes_added += 1
        except Exception as e:
            st.warning(f"Could not add geometry for {street_name}: {e}")
            continue
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
        <p style="margin: 0 0 10px 0; font-weight: bold;">Legend</p>
        <p style="margin: 5px 0;"><span style="color: #ef4444; font-size: 20px;">●</span> Increased Risk</p>
        <p style="margin: 5px 0;"><span style="color: #22c55e; font-size: 20px;">●</span> Decreased Risk</p>
        <p style="margin: 5px 0;"><span style="color: #6b7280; font-size: 20px;">●</span> No Change</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add JavaScript for Chrome rendering fix
    template = """
    {% macro script(this, kwargs) %}
    <script>
    (function() {
        console.log('[Map Init] Initializing...');
        var map = {{this._parent.get_name()}};
        var polygonBaseStyles = {};
        var polygonCounter = 0;

        // Apply global style to enhance prominence and smoothness
        var style = document.createElement('style');
        style.innerHTML = `
            .leaflet-interactive {
                transition: stroke-width 0.2s ease, fill-opacity 0.2s ease;
                stroke-linecap: round;
                stroke-linejoin: round;
            }
            .leaflet-interactive:hover {
                fill-opacity: 0.8 !important;
                stroke-width: 6 !important;
            }
        `;
        document.head.appendChild(style);
        
        // Chrome visibility fix - invalidate size when map becomes visible
        function invalidateMapSize() {
            if (map && map._container) {
                setTimeout(function() {
                    map.invalidateSize();
                    console.log('[Map Init] Size invalidated');
                }, 100);
            }
        }
        
        // Use IntersectionObserver to detect when map becomes visible
        if (window.IntersectionObserver && map._container) {
            var observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        invalidateMapSize();
                    }
                });
            }, { threshold: 0.1 });
            observer.observe(map._container);
        }
        
        // Also invalidate on window focus and resize
        window.addEventListener('focus', invalidateMapSize);
        window.addEventListener('resize', invalidateMapSize);
        
        // Invalidate immediately and after delays
        invalidateMapSize();
        setTimeout(invalidateMapSize, 500);
        setTimeout(invalidateMapSize, 1000);
        
        function updatePolygonSizes() {
            if (!map) return;
            
            var zoom = map.getZoom();
            var scaleFactor = Math.pow(2, (12 - zoom)) * 0.5;
            
            map.eachLayer(function(layer) {
                if (layer instanceof L.Polygon) {
                    if (!layer._polyScaleId) {
                        layer._polyScaleId = 'poly_' + polygonCounter++;
                        polygonBaseStyles[layer._polyScaleId] = {
                            weight: layer.options.weight || 3,
                            fillOpacity: layer.options.fillOpacity || 0.3,
                            opacity: layer.options.opacity || 0.8
                        };
                    }
                    
                    var baseStyles = polygonBaseStyles[layer._polyScaleId];
                    if (baseStyles) {
                        layer.setStyle({
                            weight: Math.max(1, baseStyles.weight * scaleFactor),
                            fillOpacity: Math.min(0.6, baseStyles.fillOpacity + (scaleFactor - 1) * 0.1),
                            opacity: Math.min(1, baseStyles.opacity + (scaleFactor - 1) * 0.1)
                        });
                    }
                }
            });
        }
        
        map.on('zoomend', updatePolygonSizes);
        map.whenReady(function() {
            setTimeout(updatePolygonSizes, 100);
        });
    })();
    </script>
    {% endmacro %}
    """
    
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)
    
    return m, routes_added

def show_abnormal_events_details(df, selected_street):
    """Display detailed analysis for selected abnormal events route"""
    if not selected_street:
        return
    
    street_data = df[df['street_name'] == selected_street]
    if street_data.empty:
        st.error(f"No data found for {selected_street}")
        return
    
    main_row = street_data.iloc[0]
    create_abnormal_detail_card(selected_street, main_row)

# ════════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ════════════════════════════════════════════════════════════════════════════════

def render_tab2():
    """Render Tab 2 - Abnormal Events Analysis"""
    
    abnormal_df = load_abnormal_events_data()
    abnormal_segments_df = load_abnormal_events_segments()
    
    if abnormal_df.empty:
        st.error("Could not load abnormal events data")
        st.info("Please ensure the dlr-abnormal-events.csv file exists in data/processed/tab2_abnormaltrend/")
        return
    
    if abnormal_segments_df is None or abnormal_segments_df.empty:
        st.error("Could not load abnormal events segment geometry")
        st.info("Please ensure the abnormal-events.geojson file exists in data/processed/tab2_abnormaltrend/")
        return
    
    # Initialize session state
    if 'abnormal_analysis' not in st.session_state:
        st.session_state.abnormal_analysis = None
    
    # Section header
    create_section_header("Abnormal Events Analysis", "Safety incidents and risk assessment across routes")
    
    # Professional metrics
    create_abnormal_metrics(abnormal_df)
    
    # Sidebar controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Tab 2: Abnormal Events Settings")
    show_cycleways = st.sidebar.checkbox("Show Cycleways", key="cycleways_abnormal", value=False)
    
    # Map section
    create_section_header("Abnormal Events Map", "Visual representation of safety incidents and risk levels")
    
    abnormal_map, routes_added = create_abnormal_events_map(abnormal_df, abnormal_segments_df, show_cycleways)
    
    if routes_added > 0:
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        map_data = st_folium(
            abnormal_map, 
            width=1200,
            height=600,
            returned_objects=["last_object_clicked_popup"],
            key="abnormal_events_map"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Check if user clicked on a popup
        clicked_street = None
        if map_data and 'last_object_clicked_popup' in map_data and map_data['last_object_clicked_popup']:
            popup_content = str(map_data['last_object_clicked_popup']).strip()
            
            # Simple direct match first
            for street_name in abnormal_df['street_name'].dropna().unique():
                if popup_content.startswith(street_name):
                    clicked_street = street_name
                    break
            
            # More robust search if direct match fails
            if not clicked_street:
                earliest_position = len(popup_content)
                for street_name in abnormal_df['street_name'].dropna().unique():
                    position = popup_content.find(street_name)
                    if position != -1 and position < earliest_position:
                        clicked_street = street_name
                        earliest_position = position
    
        if clicked_street:
            st.markdown("---")
            
            if st.button(f"View Detailed Analysis for {clicked_street}", 
                        type="primary", 
                        use_container_width=True,
                        key=f"analyze_abnormal_{clicked_street}"):
                st.session_state.abnormal_analysis = clicked_street
    else:
        st.warning("No abnormal events routes could be displayed. Please check data consistency between CSV and GeoJSON files.")
    
    # Display analysis
    if st.session_state.abnormal_analysis:
        street_name = st.session_state.abnormal_analysis
        
        if st.session_state.get('abnormal_analysis_loaded') != street_name:
            with st.spinner("Generating AI insights..."):
                import time
                time.sleep(2)
            st.session_state.abnormal_analysis_loaded = street_name
        
        show_abnormal_events_details(abnormal_df, street_name)
        
        if st.button("Close Analysis", key="close_abnormal_analysis"):
            st.session_state.abnormal_analysis = None
            st.session_state.abnormal_analysis_loaded = None

if __name__ == "__main__":
    render_tab2()