"""
Tab 3: Route Popularity Analysis - Enhanced Professional Version
Performance trends and popularity metrics for cycling routes
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.graph_objects as go
import json
import re
import os
from pathlib import Path
from branca.element import MacroElement, Template

try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# ════════════════════════════════════════════════════════════════════════════════
# PATH CONFIGURATION - Works locally and on Streamlit Cloud
# ════════════════════════════════════════════════════════════════════════════════

def get_data_path():
    """Get the correct data path whether running locally or on Streamlit Cloud"""
    # Try to find the data directory relative to the script location
    script_dir = Path(__file__).parent
    
    # Check if we're in the src directory (local development)
    if script_dir.name == 'src':
        data_dir = script_dir.parent / 'data' / 'processed' / 'tab3_routepopularity'
    else:
        # Fallback to relative path from current directory
        data_dir = Path('data') / 'processed' / 'tab3_routepopularity'
    
    return data_dir

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

def create_route_metrics(df):
    """Create professional metrics for route analysis"""
    col1, col2, col3, col4 = st.columns(4)
    
    total_routes = len(df['street_name'].unique()) if not df.empty else 0
    popular_routes = len(df[df['Colour'] == 'Green']) if not df.empty else 0
    declined_routes = len(df[df['Colour'] == 'Red']) if not df.empty else 0
    avg_trips = int(df['trips_count'].mean()) if not df.empty and 'trips_count' in df.columns else 0
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Routes</div>
            <div class="kpi-value">{total_routes}</div>
            <div class="kpi-change">Active Monitoring</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Popular Routes</div>
            <div class="kpi-value">{popular_routes}</div>
            <div class="kpi-change positive">High Traffic</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Declined Routes</div>
            <div class="kpi-value">{declined_routes}</div>
            <div class="kpi-change negative">Lower Traffic</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Weekly Trips</div>
            <div class="kpi-value">{avg_trips:,}</div>
            <div class="kpi-change">Per Route</div>
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# DATA LOADING FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_time_of_day_data():
    """Load time of day data from JSON"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "time-of-the-day.json"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            st.warning(f"Time of day data not found at: {file_path}")
            return []
    except Exception as e:
        st.warning(f"Could not load time of day data: {e}")
        return []

@st.cache_data
def load_day_of_week_data():
    """Load day of week data from JSON"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "day-of-the-week.json"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            st.warning(f"Day of week data not found at: {file_path}")
            return {}
    except Exception as e:
        st.warning(f"Could not load day of week data: {e}")
        return {}

@st.cache_data
def load_street_trends_metadata():
    """Load street trends metadata from JSON"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "weekly_street_trends.json"
        
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            st.warning(f"Street trends metadata not found at: {file_path}")
            return {}
    except Exception as e:
        st.warning(f"Could not load street trends metadata: {e}")
        return {}

@st.cache_data
def load_daily_street_data():
    """Load daily street data from CSV"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "daily_street_data.csv"
        
        if file_path.exists():
            df = pd.read_csv(file_path)
            # Convert date column to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        else:
            st.warning(f"Daily street data not found at: {file_path}")
            return pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not load daily street data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_cycleways_data():
    """Load cycleways GeoJSON as dict to avoid PROJ issues"""
    try:
        data_dir = get_data_path()
        paths = [
            data_dir / "dublin-cycleways.geojson",
            data_dir.parent / "dublin-cycleways.geojson",
            data_dir.parent / "tab2_abnormaltrend" / "dublin-cycleways.geojson",
            Path("/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/dublin-cycleways.geojson")
        ]
        
        for path in paths:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        return None
    except Exception:
        return None

@st.cache_data
def load_road_segments():
    """Load road segments GeoJSON - with fallback for PROJ errors"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "trimmed_active_segments.geojson"
        
        if not file_path.exists():
            st.warning(f"Road segments GeoJSON not found at: {file_path}")
            return gpd.GeoDataFrame()
        
        # Try loading with GeoDataFrame first
        try:
            # Load as JSON first to avoid PROJ errors
            with open(file_path, 'r') as f:
                geojson_data = json.load(f)
            
            # Convert to GeoDataFrame without setting CRS initially
            gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
            
            # Set CRS to WGS84 (EPSG:4326) without validation
            try:
                gdf.crs = "EPSG:4326"
            except:
                # If CRS setting fails, continue without it (coordinates are still valid)
                pass
            
            return gdf
            
        except Exception as gdf_error:
            # Fallback: create a simple DataFrame with geometry info
            st.info(f"Using fallback GeoJSON loader (GeoPandas issue: {str(gdf_error)[:100]})")
            
            with open(file_path, 'r') as f:
                geojson_data = json.load(f)
            
            # Create a simple dataframe with the data we need
            features = []
            for feature in geojson_data.get('features', []):
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                
                features.append({
                    'street_name': props.get('street_name', ''),
                    'original_clean_name': props.get('original_clean_name', ''),
                    'geometry': geom,
                    'geometry_type': geom.get('type', ''),
                    'coordinates': geom.get('coordinates', [])
                })
            
            df = pd.DataFrame(features)
            return df
            
    except Exception as e:
        st.error(f"Could not load road segments: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

@st.cache_data
def load_route_popularity_data():
    """Load route popularity data from dlr-route-popularity.csv"""
    try:
        data_dir = get_data_path()
        file_path = data_dir / "dlr-route-popularity.csv"
        
        if not file_path.exists():
            st.error(f"Route popularity CSV not found at: {file_path}")
            return pd.DataFrame()
        
        # Read CSV with proper handling of multi-line fields
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Rename columns for consistency
        df = df.rename(columns={
            'Street Name': 'street_name',
            'Popularity Change': 'popularity_change',
            'Consistency (R²)': 'consistency',
            'Total Volume': 'total_volume',
            'Peak': 'peak',
            'Biggest Spike/Drop': 'spike_drop',
            'AI Summary': 'ai_summary',
            'Weather Impact': 'weather_impact'
        })
        
        # Strip whitespace from street names for robust matching
        df['street_name'] = df['street_name'].str.strip()
        
        # Determine color based on popularity change
        def get_color(change_text):
            if pd.isna(change_text):
                return 'Gray'
            change_lower = str(change_text).lower()
            if 'increasing' in change_lower or 'improved' in change_lower:
                return 'Green'
            elif 'decreasing' in change_lower or 'dropped' in change_lower or 'decline' in change_lower:
                return 'Red'
            else:
                return 'Gray'
        
        df['Colour'] = df['popularity_change'].apply(get_color)
        
        # Extract numeric trips count from total_volume
        def extract_trips(volume_text):
            if pd.isna(volume_text):
                return 0
            import re
            # Extract number with commas removed
            match = re.search(r'([\d,]+)\s*rides?', str(volume_text))
            if match:
                return int(match.group(1).replace(',', ''))
            return 0
        
        df['trips_count'] = df['total_volume'].apply(extract_trips)
        
        # Add fields for compatibility
        df['peak_trips'] = df['spike_drop'].fillna('No spike/drop data')
        df['summary'] = df['ai_summary'].fillna('No summary available')
        df['weather_impact_note'] = df['weather_impact'].fillna('No weather data')
        
        # Add placeholder for speed (not in this CSV)
        df['daily_speed_mean'] = 20.0  # Default value
        
        # Debug: print street names
        #st.sidebar.text(f"Loaded {len(df)} streets from CSV")
        
        return df
        
    except Exception as e:
        st.error(f"Error loading route popularity data: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

def create_route_detail_card(street_name, row):
    """Create professional route detail cards with matplotlib trend visualization"""
    
    # Load additional data for new cards
    time_of_day_data = load_time_of_day_data()
    day_of_week_data = load_day_of_week_data()
    street_trends_metadata = load_street_trends_metadata()
    daily_street_data = load_daily_street_data()
    
    # Get peak vs non-peak data for this street
    traffic_type = "N/A"
    peak_percentage = 0
    non_peak_percentage = 0
    for item in time_of_day_data:
        if item.get('street') == street_name:
            peak_percentage = item.get('peak_non_peak', {}).get('peak', 0)
            non_peak_percentage = item.get('peak_non_peak', {}).get('non_peak', 0)
            traffic_type = "Commuter" if peak_percentage >= non_peak_percentage else "Leisure"
            break
    
    # Get time of day breakdown
    morning = afternoon = evening = night = 0
    for item in time_of_day_data:
        if item.get('street') == street_name:
            time_dist = item.get('time_of_day', {})
            morning = time_dist.get('morning', 0)
            afternoon = time_dist.get('afternoon', 0)
            evening = time_dist.get('evening', 0)
            night = time_dist.get('night', 0)
            break
    
    # Create the main card container
    with st.container():
        # Card header with centered road name
        st.markdown(f"""
        <div style="background: light grey; border-radius: 8px; padding: 2rem; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2rem;">
            <div style="text-align: center;">
                <h3 style="margin: 0 0 0rem 0; color: #1f2937; font-weight: 600; font-size: 2.5rem;">{street_name}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        color = row.get('Colour', 'Gray')
        trips_count = row.get('trips_count', 0)
        popularity_change = row.get('popularity_change', 'N/A')
        consistency = row.get('consistency', 'N/A')
        peak_info = row.get('peak', 'No data available')
        
        # Card hover style
        card_hover_style = """
        <style>
        .metric-card-hover {
            text-align: center; 
            background: #f8fafc; 
            padding: 1.5rem; 
            border-radius: 8px; 
            margin: 0.5rem;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }
        .metric-card-hover:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            background: #f1f5f9;
            border: 1px solid #e5e7eb;
        }
        </style>
        """
        st.markdown(card_hover_style, unsafe_allow_html=True)
        
        # Metrics using 4 columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card-hover">
                <div style="font-size: 1.05rem; color: #6b7280; font-weight: 600; margin-bottom: 0.75rem;">Total Volume</div>
                <div style="font-size: 1.50rem; font-weight: 700; color: #1f2937;">{trips_count:,}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card-hover">
                <div style="font-size: 1.05rem; color: #6b7280; font-weight: 600; margin-bottom: 0.75rem;">Traffic Type</div>
                <div style="font-size: 1.50rem; font-weight: 700; color: #1f2937;">{traffic_type}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card-hover">
                <div style="font-size: 1.05rem; color: #6b7280; font-weight: 600; margin-bottom: 0.75rem;">Peak Period</div>
                <div style="font-size: 1.50rem; font-weight: 700; color: #1f2937;">{peak_info}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            trend_color = '#22c55e' if color == 'Green' else '#ef4444'
            st.markdown(f"""
            <div class="metric-card-hover">
                <div style="font-size: 1.05rem; color: #6b7280; font-weight: 600; margin-bottom: 0.75rem;">Trend</div>
                <div style="font-size: 1.50rem; font-weight: 700; color: {trend_color};">{popularity_change.split('(')[0].strip()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Close the card container
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Additional Metrics Section - Professional Display
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            popularity_change = row.get('popularity_change', 'N/A')
            st.markdown(f"""
            <div style="background: #f9fafb; border-radius: 8px; padding: 1.5rem; border: 1px solid #e5e7eb;">
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 600; margin-bottom: 0.5rem;">Popularity Change</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{popularity_change}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metrics_col2:
            consistency = row.get('consistency', 'N/A')
            # Show full decimal precision for consistency
            try:
                consistency_val = f"{float(consistency):.3f}" if consistency != 'N/A' and consistency else 'N/A'
            except:
                consistency_val = str(consistency)
            st.markdown(f"""
            <div style="background: #f9fafb; border-radius: 8px; padding: 1.5rem; border: 1px solid #e5e7eb;">
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 600; margin-bottom: 0.5rem;">Consistency (R²)</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{consistency_val}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metrics_col3:
            spike_drop = row.get('spike_drop', 'N/A')
            st.markdown(f"""
            <div style="background: #f9fafb; border-radius: 8px; padding: 1.5rem; border: 1px solid #e5e7eb;">
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 600; margin-bottom: 0.5rem;">Biggest Spike/Drop</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #1f2937;">{spike_drop}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # AI Summary Section - Clean, Plain Display
        ai_summary = row.get('ai_summary', row.get('summary', 'No summary available'))
        if ai_summary and str(ai_summary) != 'No summary available' and not pd.isna(ai_summary):
            st.markdown("<div style='margin-bottom: 2rem; margin-top: 2rem;'></div>", unsafe_allow_html=True)
            st.markdown("### AI Analysis")
            
            # Clean up the AI summary - replace excessive newlines with proper spacing
            clean_summary = str(ai_summary).strip()
            # Replace multiple newlines with double newlines for paragraph breaks
            clean_summary = re.sub(r'\n{3,}', '\n\n', clean_summary)
            
            # Display AI summary as plain text
            st.markdown(f"""
            <div style="color: #1f2937; font-size: 1rem; line-height: 1.6; margin-bottom: 2rem;">
                {clean_summary}
            </div>
            """, unsafe_allow_html=True)
        
        # Weather Impact if available - Plain display
        weather_impact = row.get('weather_impact', row.get('weather_impact_note', ''))
        if weather_impact and str(weather_impact) != 'No weather data' and not pd.isna(weather_impact):
            st.markdown("**Weather Impact**")
            # Display weather impact as plain text
            st.markdown(f"""
            <div style="color: #374151; font-size: 1rem; line-height: 1.5; margin-bottom: 1.5rem;">
                {weather_impact}
            </div>
            """, unsafe_allow_html=True)
        
        # MATPLOTLIB TREND ANALYSIS SECTION - WEEKLY DATA FROM METADATA
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("### Trend Analysis")
        
        # Strip whitespace for matching
        lookup_street = street_name.strip()
        
        # Check if we have trend data for this street in metadata
        if lookup_street in street_trends_metadata:
            street_data = street_trends_metadata[lookup_street]
            weekly_data = street_data.get('weekly', [])
            
            if weekly_data and len(weekly_data) > 0:
                weekly_df = pd.DataFrame(weekly_data)
                weekly_df['date'] = pd.to_datetime(weekly_df['date'])
                weekly_df = weekly_df.sort_values('date')
                
                # Use popularity_score from the new JSON structure
                score_col = 'popularity_score' if 'popularity_score' in weekly_df.columns else 'daily_popularity'
                
                # Filter for 2025 data as requested - keep zero values to show full trend
                weekly_df_filtered = weekly_df[
                    (weekly_df['date'] >= '2025-01-01') & 
                    (weekly_df['date'] <= '2025-12-31')
                ].copy()
                
                if len(weekly_df_filtered) >= 1: # Show graph even if 1 point exist (for x-axis range)
                    # Apply 3-week rolling average for smoothing if we have enough points
                    if len(weekly_df_filtered) >= 3:
                        weekly_df_filtered['smoothed'] = weekly_df_filtered[score_col].rolling(
                            window=3, center=True, min_periods=1
                        ).mean()
                    else:
                        weekly_df_filtered['smoothed'] = weekly_df_filtered[score_col]
                    
                    # Find peaks on smoothed data
                    rolling_values = weekly_df_filtered['smoothed'].values
                    peak_indices = []
                    for i in range(1, len(rolling_values) - 1):
                        if rolling_values[i] > rolling_values[i-1] and rolling_values[i] > rolling_values[i+1]:
                            peak_indices.append(i)
                    
                    # Create matplotlib figure
                    fig, ax = plt.subplots(figsize=(12, 5))
                    
                    # Plot original weekly data (faint)
                    ax.plot(weekly_df_filtered['date'], weekly_df_filtered[score_col], 
                            color="#b7bc27f4", alpha=0.3, linewidth=1.5, marker='o', markersize=4, 
                            label='Weekly data')
                    
                    # Plot smoothed trend (bold)
                    ax.plot(weekly_df_filtered['date'], weekly_df_filtered['smoothed'], 
                            color='#2563eb', linewidth=3, label='3-week rolling average')
                    
                    # Highlight peaks
                    if peak_indices:
                        peak_dates = weekly_df_filtered.iloc[peak_indices]['date']
                        peak_values = weekly_df_filtered.iloc[peak_indices]['smoothed']
                        ax.scatter(peak_dates, peak_values, 
                                  color='#dc2626', s=50, zorder=5, marker='D', label='Peaks')
                    
                    # Customize the plot
                    ax.set_title(f'{street_name} - Weekly Popularity Trend', fontsize=14, fontweight='normal', pad=20)
                    ax.set_ylabel('Popularity Score', fontsize=11, color='#6b7280')
                    ax.set_xlabel('Date', fontsize=11, color='#6b7280')
                    ax.grid(True, alpha=0.3, linestyle='--')

                    # Make axis borders grey
                    ax.spines['bottom'].set_color('#6b7280')
                    ax.spines['top'].set_color('#6b7280') 
                    ax.spines['right'].set_color('#6b7280')
                    ax.spines['left'].set_color('#6b7280')
                    
                    # Make tick labels grey
                    ax.tick_params(axis='both', colors='#6b7280')

                    # Format x-axis dates - set range from Jan 2025 to Dec 2025
                    ax.set_xlim([pd.to_datetime('2025-01-01'), pd.to_datetime('2025-12-31')])
                    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                    plt.xticks(rotation=45, ha='right')
                    
                    # Add legend
                    ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
                    
                    # Set background to white
                    fig.patch.set_facecolor('white')
                    ax.set_facecolor('white')
                    
                    # Adjust layout
                    plt.tight_layout()
                    
                    # Display the matplotlib figure
                    st.pyplot(fig)
                    
                    # Clear the figure
                    plt.close(fig)
                elif len(weekly_df_filtered) > 0:
                    st.info(f"Limited data available: only {len(weekly_df_filtered)} weeks with recorded activity")
                else:
                    st.info("No weekly data available for this street (all values are zero)")
                
            else:
                st.info("No weekly trend data available for this street")
        else:
            st.info("No trend data available for this street")
        
        # Temporal Analysis Section
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown("### Temporal Analysis")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Day of Week Bar Chart using day-of-the-week.json
            day_of_week_street_data = day_of_week_data.get(street_name, {})
            day_totals = day_of_week_street_data.get('day_totals', {})
            
            if day_totals and sum(day_totals.values()) > 0:
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                days_display = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                
                # Get values for each day
                values = [day_totals.get(day, 0) for day in days_order]
                
                fig_bar = go.Figure(data=[
                    go.Bar(
                        x=days_display,
                        y=values,
                        marker_color='#3b82f6',
                        hovertemplate='<b>%{x}</b><br>Trips: %{y:,}<extra></extra>'
                    )
                ])
                
                fig_bar.update_layout(
                    title='Trip Volume by Day of Week',
                    xaxis_title='Day',
                    yaxis_title='Trip Count',
                    height=350,
                    margin=dict(l=40, r=40, t=50, b=40),
                    font=dict(size=12),
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                fig_bar.update_xaxes(tickangle=0)
                
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No day of week data available for this street")
        
        with chart_col2:
            # Peak vs Non-Peak Pie Chart
            if peak_percentage > 0 or non_peak_percentage > 0:
                fig_pie = go.Figure(data=[
                    go.Pie(
                        labels=['Peak', 'Non Peak'],
                        values=[peak_percentage, non_peak_percentage],
                        hole=0.4,
                        marker_colors=['#3b82f6', '#8b5cf6'],
                        hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>'
                    )
                ])
                
                fig_pie.update_layout(
                    title='Peak vs Non Peak Traffic Distribution',
                    height=350,
                    margin=dict(l=40, r=40, t=50, b=40),
                    font=dict(size=12),
                    paper_bgcolor='white'
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No peak/non-peak data available for this street")

def get_color_for_route(color):
    """Convert route color to map color"""
    color_map = {
        'Green': '#22c55e',
        'Red': '#ef4444',
        'Gray': '#9ca3af'
    }
    return color_map.get(color, '#9ca3af')

def create_route_map(df, road_segments_df, show_cycleways=False):
    """Create interactive map with route segments"""
    
    if df.empty or road_segments_df.empty:
        dublin_center = [53.2913, -6.1360]
        return folium.Map(location=dublin_center, zoom_start=13, tiles='CartoDB positron'), 0
    
    # Check if we have a GeoDataFrame or regular DataFrame
    is_geodataframe = isinstance(road_segments_df, gpd.GeoDataFrame)
    
    # Calculate map center
    dublin_center = [53.2913, -6.1360]
    
    m = folium.Map(
        location=dublin_center,
        zoom_start=12,
        tiles='CartoDB positron'
    )
    
    # Add cycleways if requested
    if show_cycleways:
        cycleways_data = load_cycleways_data()
        if cycleways_data:
            try:
                folium.GeoJson(
                    cycleways_data,
                    name="Cycleways",
                    style_function=lambda x: {
                        'color': '#3b82f6',
                        'weight': 3,
                        'opacity': 0.7
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['name'] if 'name' in str(cycleways_data) else [],
                        aliases=['Cycleway'] if 'name' in str(cycleways_data) else []
                    ) if 'features' in cycleways_data else None
                ).add_to(m)
            except Exception as e:
                # Silent fail for map layers to prevent crash
                pass
    
    routes_added = 0
    
    # Add route segments
    for idx, row_data in df.iterrows():
        street_name = row_data['street_name']
        color = row_data['Colour']
        trips_count = row_data['trips_count']
        
        # Find matching geometry
        matching_segments = road_segments_df[road_segments_df['street_name'] == street_name]
        
        if matching_segments.empty:
            continue
        
        # Determine status text
        status_text = "Highly Popular" if color == 'Green' else "Popularity Dropped"
        peak_info = row_data.get('peak_trips', row_data.get('summary', 'No data available'))
        
        # Create popup with route information - matching original style
        popup_html = f"""
        <div style="width: 350px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.5;">
            <h4 style="margin: 0 0 16px 0; color: {get_color_for_route(color)}; 
                       font-size: 18px; font-weight: 600;">
                {street_name}
            </h4>
            
            <div style="margin-bottom: 16px;">
                <div style="margin-bottom: 12px;">
                    <strong>Status:</strong> <span style="color: {get_color_for_route(color)}; font-weight: 600;">{status_text}</span>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <strong>Note:</strong><br>
                    <div style="font-size: 14px; color: #374151; line-height: 1.4; margin-top: 8px;">
                        {str(peak_info)}
                    </div>
                </div>
            </div>
        </div>
        """
        
        for _, segment in matching_segments.iterrows():
            # Get geometry based on data type
            if is_geodataframe:
                geometry = segment.geometry
                geometry_type = geometry.geom_type
                
                if geometry_type == 'MultiLineString':
                    for line in geometry.geoms:
                        coords = [[point[1], point[0]] for point in line.coords]
                        folium.PolyLine(
                            locations=coords,
                            color=get_color_for_route(color),
                            weight=5,
                            opacity=0.8,
                            popup=folium.Popup(popup_html, max_width=400),
                            tooltip=street_name
                        ).add_to(m)
                
                elif geometry_type == 'Point':
                    coords = [geometry.y, geometry.x]
                    folium.CircleMarker(
                        location=coords,
                        radius=8,
                        color=get_color_for_route(color),
                        fill=True,
                        fillColor=get_color_for_route(color),
                        fillOpacity=0.7,
                        popup=folium.Popup(popup_html, max_width=400),
                        tooltip=street_name
                    ).add_to(m)
                
                elif geometry_type == 'LineString':
                    coords = [[point[1], point[0]] for point in geometry.coords]
                    folium.PolyLine(
                        locations=coords,
                        color=get_color_for_route(color),
                        weight=5,
                        opacity=0.8,
                        popup=folium.Popup(popup_html, max_width=400),
                        tooltip=street_name
                    ).add_to(m)
            
            else:
                # Handle regular DataFrame with geometry dict
                geometry_type = segment.get('geometry_type', '')
                coordinates = segment.get('coordinates', [])
                
                if geometry_type == 'MultiLineString' and coordinates:
                    for line_coords in coordinates:
                        if line_coords:  # Make sure line_coords is not empty
                            coords = [[point[1], point[0]] for point in line_coords]
                            folium.PolyLine(
                                locations=coords,
                                color=get_color_for_route(color),
                                weight=5,
                                opacity=0.8,
                                popup=folium.Popup(popup_html, max_width=400),
                                tooltip=street_name
                            ).add_to(m)
                
                elif geometry_type == 'Point' and coordinates:
                    if len(coordinates) >= 2:
                        coords = [coordinates[1], coordinates[0]]
                        folium.CircleMarker(
                            location=coords,
                            radius=8,
                            color=get_color_for_route(color),
                            fill=True,
                            fillColor=get_color_for_route(color),
                            fillOpacity=0.7,
                            popup=folium.Popup(popup_html, max_width=400),
                            tooltip=street_name
                        ).add_to(m)
                
                elif geometry_type == 'LineString' and coordinates:
                    coords = [[point[1], point[0]] for point in coordinates]
                    folium.PolyLine(
                        locations=coords,
                        color=get_color_for_route(color),
                        weight=5,
                        opacity=0.8,
                        popup=folium.Popup(popup_html, max_width=400),
                        tooltip=street_name
                    ).add_to(m)
        
        routes_added += 1
    
    # Add legend - matching original style
    if routes_added > 0:
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; 
                    background-color: white; border: 1px solid #d1d5db; z-index:9999; 
                    font-size: 14px; padding: 16px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <div style="font-weight: 600; margin-bottom: 12px; color: #111827;">Route Performance</div>
        <div style="margin-bottom: 8px;">
            <span style="display: inline-block; width: 16px; height: 3px; background-color: #22c55e; margin-right: 8px;"></span>
            <span style="color: #374151;">Highly Popular</span>
        </div>
        <div style="margin-bottom: 8px;">
            <span style="display: inline-block; width: 16px; height: 3px; background-color: #ef4444; margin-right: 8px;"></span>
            <span style="color: #374151;">Popularity Dropped</span>
        </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, routes_added

def show_route_details(df, selected_street):
    """Display detailed analysis for selected route"""
    if not selected_street:
        return
    
    street_data = df[df['street_name'] == selected_street]
    if street_data.empty:
        st.error(f"No data found for {selected_street}")
        return
    
    row = street_data.iloc[0]
    create_route_detail_card(selected_street, row)

# ════════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ════════════════════════════════════════════════════════════════════════════════

def render_tab3():
    """Render Tab 3 - Route Popularity Analysis"""
    
    df = load_route_popularity_data()
    road_segments_df = load_road_segments()
    
    if df.empty:
        st.error("Could not load route popularity data")
        st.info("Please ensure the CSV file exists and contains the required data")
        return
    
    # Check if road_segments_df is empty (works for both DataFrame types)
    is_empty = road_segments_df.empty if hasattr(road_segments_df, 'empty') else len(road_segments_df) == 0
    
    if is_empty:
        st.error("Could not load road segment geometry")
        st.info("Please ensure the trimmed_active_segments.geojson file exists")
        return
    
    # Initialize session state
    if 'route_analysis' not in st.session_state:
        st.session_state.route_analysis = None
    
    # Section header
    create_section_header("Change in Route Popularity Analysis", "Performance trends and popularity metrics for cycling routes")
    
    # Professional metrics
    create_route_metrics(df)
    
    # Sidebar controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Tab 3: Change in Route Popularity Settings")
    show_cycleways = st.sidebar.checkbox("Show Cycleways", key="tab3_cycleways_route", value=False)
    
    # Map section
    create_section_header("Route Performance Map", "Visual representation of route popularity and performance")
    
    route_map, routes_added = create_route_map(df, road_segments_df, show_cycleways)
    
    if routes_added > 0:
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        map_data = st_folium(
            route_map, 
            width=1200,
            height=600,
            returned_objects=["last_object_clicked_popup"],
            key="tab3_route_map"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Check if user clicked on a popup
        clicked_street = None
        if map_data and 'last_object_clicked_popup' in map_data and map_data['last_object_clicked_popup']:
            popup_content = str(map_data['last_object_clicked_popup'])
            
            for street_name in df['street_name'].tolist():
                if popup_content.strip().startswith(street_name):
                    clicked_street = street_name
                    break
            
            if not clicked_street:
                earliest_position = len(popup_content)
                for street_name in df['street_name'].tolist():
                    position = popup_content.find(street_name)
                    if position != -1 and position < earliest_position:
                        clicked_street = street_name
                        earliest_position = position
        
        if clicked_street:
            st.markdown("---")
            
            if st.button(f"View Detailed Analysis for {clicked_street}", 
                        type="primary", 
                        use_container_width=True,
                        key=f"analyze_{clicked_street}"):
                st.session_state.route_analysis = clicked_street
                st.rerun()
    
    else:
        st.warning("No routes could be displayed. Please check data consistency between CSV and GeoJSON files.")
    
    # Display analysis
    if st.session_state.route_analysis:
        street_name = st.session_state.route_analysis
        
        if st.session_state.get('route_analysis_loaded') != street_name:
            with st.spinner("Generating insights..."):
                import time
                time.sleep(1)
            st.session_state.route_analysis_loaded = street_name
        
        show_route_details(df, street_name)
        
        if st.button("Close Analysis", key="close_route_analysis", use_container_width=True):
            st.session_state.route_analysis = None
            st.session_state.route_analysis_loaded = None

if __name__ == "__main__":
    render_tab3()