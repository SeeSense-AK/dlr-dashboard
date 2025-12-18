#!/usr/bin/env python3
"""
Use this for trend graph and day of the week extraction for tab 3 - route popularity.
This script extracts street trends metadata from the Tab 3 route popularity data.
It properly aggregates daily street data to match the day-of-week calculations.
"""

import pandas as pd
import json
from datetime import datetime
import os

# Define file paths
data_dir = "/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/tab3_routepopularity"
popularity_file = os.path.join(data_dir, "dlr-route-popularity.csv")
daily_file = os.path.join(data_dir, "daily_street_data.csv")
output_file = os.path.join(data_dir, "street_trends_metadata_tab3.json")

# Manual mapping dictionary for street combinations
STREET_MAPPING = {
    "West Pier": ["West Pier"],
    "Leopardstown Road": ["Leopardstown Road"],
    "Puck's Castle Lane": ["Puck's Castle Lane"],
    "Blackthorn Avenue / Burton Hall Road / Blackthorn Road / Blackthorn Drive": [
        "Blackthorn Avenue", 
        "Burton Hall Road", 
        "Blackthorn Road", 
        "Blackthorn Drive"
    ],
    "Leopardstown Avenue": ["Leopardstown Avenue"],
    "Clonskeagh Road": ["Clonskeagh Road"],
    "Nutley Lane": ["Nutley Lane"]
}

def split_street_name(combined_name):
    """Use manual mapping for street names"""
    if combined_name in STREET_MAPPING:
        return STREET_MAPPING[combined_name]
    else:
        return [combined_name.strip()]

def convert_to_serializable(obj):
    """Convert objects to JSON serializable formats"""
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif hasattr(obj, 'dtype'):
        return float(obj) if 'float' in str(obj.dtype) else int(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    else:
        return str(obj)

def extract_street_trends_metadata():
    # Read both files
    file_a = pd.read_csv(popularity_file)  # dlr-route-popularity.csv
    file_b = pd.read_csv(daily_file)       # daily_street_data.csv
    
    # Convert date column to datetime
    file_b['date'] = pd.to_datetime(file_b['date'])
    
    # Get available streets from file_b for debugging
    available_streets = file_b['road_name'].unique().tolist()
    print(f"Available streets in daily_street_data.csv: {len(available_streets)}")
    
    trends_metadata = {}
    
    for idx, street_row in file_a.iterrows():
        combined_street_name = street_row['Street Name']
        
        # Get popularity info
        popularity_change = street_row.get('Popularity Change', 'N/A')
        total_volume = street_row.get('Total Volume', 'N/A')
        consistency = street_row.get('Consistency (R²)', 'N/A')
        
        print(f"\nProcessing: {combined_street_name}")
        
        # Use manual mapping to get component streets
        individual_streets = split_street_name(combined_street_name)
        print(f"  Looking for: {individual_streets}")
        
        # Check which streets actually exist in file_b
        existing_streets = [street for street in individual_streets 
                           if any(available in street or street in available 
                                 for available in available_streets)]
        print(f"  Existing matches: {existing_streets}")
        
        if not existing_streets:
            print(f"  ⚠️  No matching streets found in data!")
            continue
        
        # Filter file_b for the existing streets - using partial matching
        mask = file_b['road_name'].str.contains('|'.join(existing_streets), case=False, na=False)
        street_data = file_b[mask].copy()
        
        if len(street_data) == 0:
            print(f"  ⚠️  No data after filtering")
            continue
        
        print(f"  Found {len(street_data)} records")
        
        # Group by date to match the day-of-week calculation
        # This is the KEY FIX: group by date to aggregate multiple records per day
        daily_aggregated = street_data.groupby('date').agg({
            'daily_popularity': 'mean',
            'daily_cyclists': 'sum',  # SUM cyclists per day
            'daily_rides': 'sum',
            'daily_points': 'sum',
            'daily_speed': 'mean'
        }).reset_index()
        
        daily_aggregated = daily_aggregated.sort_values('date')
        
        # Calculate weekly pattern (should match day-of-week.json)
        street_data['day_of_week'] = street_data['date'].dt.day_name()
        weekly_pattern = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            day_data = street_data[street_data['day_of_week'] == day]
            weekly_pattern[day.lower()] = int(day_data['daily_cyclists'].sum())
        
        # Create aggregated trends
        daily = daily_aggregated.copy()
        
        weekly = daily_aggregated.set_index('date').resample('W').agg({
            'daily_popularity': 'mean',
            'daily_cyclists': 'sum',
            'daily_rides': 'sum',
            'daily_points': 'sum',
            'daily_speed': 'mean'
        }).reset_index()
        
        monthly = daily_aggregated.set_index('date').resample('ME').agg({
            'daily_popularity': 'mean',
            'daily_cyclists': 'sum',
            'daily_rides': 'sum',
            'daily_points': 'sum',
            'daily_speed': 'mean'
        }).reset_index()
        
        # Calculate totals
        total_cyclists = int(daily_aggregated['daily_cyclists'].sum())
        
        # Convert to serializable format
        daily_serializable = convert_to_serializable(daily)
        weekly_serializable = convert_to_serializable(weekly)
        monthly_serializable = convert_to_serializable(monthly)
        
        # Store metadata
        trends_metadata[combined_street_name] = {
            'daily': daily_serializable,
            'weekly': weekly_serializable,
            'monthly': monthly_serializable,
            'popularity_info': {
                'popularity_change': str(popularity_change),
                'total_volume': str(total_volume),
                'consistency': str(consistency)
            },
            'component_streets': individual_streets,
            'existing_component_streets': existing_streets,
            'stats': {
                'total_days': len(daily_aggregated),
                'total_records': len(street_data),
                'component_streets_found': existing_streets,
                'date_range': {
                    'start': daily_aggregated['date'].min().strftime('%Y-%m-%d'),
                    'end': daily_aggregated['date'].max().strftime('%Y-%m-%d')
                },
                'avg_popularity': float(daily_aggregated['daily_popularity'].mean()),
                'max_popularity': float(daily_aggregated['daily_popularity'].max()),
                'min_popularity': float(daily_aggregated['daily_popularity'].min()),
                'total_cyclists': total_cyclists,
                'total_points': int(daily_aggregated['daily_points'].sum()),
                'avg_speed': float(daily_aggregated['daily_speed'].mean()),
                'weekly_pattern': weekly_pattern
            }
        }
        
        print(f"  ✅ Success: {len(street_data)} raw records -> {len(daily_aggregated)} days")
        print(f"  Date range: {daily_aggregated['date'].min().date()} to {daily_aggregated['date'].max().date()}")
        print(f"  Total cyclists: {total_cyclists:,}")
        print(f"  Weekly pattern matches day-of-week.json: {total_cyclists == sum(weekly_pattern.values())}")
    
    return trends_metadata

# Run the extraction
if __name__ == "__main__":
    print("="*60)
    print("FIXED: Tab 3 Street Trends Metadata Extractor")
    print("="*60)
    
    print("Extracting street trends metadata...")
    print(f"Reading from: {data_dir}")
    
    metadata = extract_street_trends_metadata()
    
    # Save metadata
    with open(output_file, 'w') as f:
        json.dump(convert_to_serializable(metadata), f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Metadata saved to: {output_file}")
    
    # Compare with day-of-week.json
    day_of_week_file = os.path.join(data_dir, "trend.json")
    if os.path.exists(day_of_week_file):
        with open(day_of_week_file, 'r') as f:
            day_data = json.load(f)
        
        print(f"\n{'='*60}")
        print("VALIDATION: Comparing with day-of-week.json")
        print(f"{'='*60}")
        
        for street in metadata.keys():
            if street in day_data:
                meta_total = metadata[street]['stats']['total_cyclists']
                day_total = day_data[street]['total_cyclists']
                match = "✅" if meta_total == day_total else "❌ MISMATCH"
                print(f"{street}:")
                print(f"  Metadata: {meta_total:,} cyclists")
                print(f"  Day-of-week: {day_total:,} cyclists")
                print(f"  {match}")
                
                if meta_total != day_total:
                    print(f"  Difference: {abs(meta_total - day_total):,} cyclists")
            else:
                print(f"{street}: ❌ Not found in day-of-week.json")
    
    print(f"\n{'='*60}")
    print(f"🎯 Total streets processed: {len(metadata)}")
    print(f"{'='*60}")