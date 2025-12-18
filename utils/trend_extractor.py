#!/usr/bin/env python3
"""
This script analyzes daily cycling data to calculate day-of-week trends for specific streets.
It processes daily street activity data and route popularity information to generate
a JSON file showing cyclist volume by day of week for streets identified in the
route popularity dataset. The output is used for trend analysis and visualization
in the DLR dashboard.

Inputs:
    - daily_street_data.csv: Daily cycling metrics per street
    - dlr-route-popularity.csv: Street popularity rankings and trends

Output:
    - trend.json: JSON file with daily cyclist totals for each day of week per street

Key Features:
    - Handles intersection names with '&' separators
    - Handles alternative street names with '/' separators
    - Aggregates data across street name variants
    - Calculates Monday-Sunday cyclist totals
    - Outputs structured JSON for dashboard consumption
"""

import pandas as pd
import json
from datetime import datetime
import os
import re

# Define file paths
data_dir = "/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/tab3_routepopularity"
daily_file = os.path.join(data_dir, "daily_street_data.csv")
popularity_file = os.path.join(data_dir, "dlr-route-popularity.csv")
output_file = os.path.join(data_dir, "trend.json")

# Load your datasets
print(f"Loading data from: {data_dir}")
df = pd.read_csv(daily_file)
df2 = pd.read_csv(popularity_file)

# Get the list of streets from df2 (using 'Street Name' column)
target_streets = df2['Street Name'].unique().tolist()
print(f"Target streets: {len(target_streets)} streets found")
print(f"First few: {target_streets[:5]}")

# Convert date column to datetime and extract day of week
df['date'] = pd.to_datetime(df['date'])
df['day_of_week'] = df['date'].dt.day_name()

# Define the days order for consistent output
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Function to handle street name variations
def get_street_variants(street_name):
    """
    Extract all street name variations from a string.
    Handles:
    - Intersections: 'Mercer Street & Cuffe Street'
    - Alternative names: 'Blackthorn Avenue / Burton Hall Road / Blackthorn Road / Blackthorn Drive'
    - Simple single street names
    """
    variants = []
    
    if not isinstance(street_name, str):
        return variants
    
    # First check for '/' separators (alternative names)
    if '/' in street_name:
        # Split by '/' and clean up
        parts = [part.strip() for part in street_name.split('/')]
        variants.extend(parts)
    
    # Also check for '&' separators (intersections)
    elif '&' in street_name:
        # Split by '&' and clean up
        parts = [part.strip() for part in street_name.split('&')]
        variants.extend(parts)
    
    # If no separators found, use the whole string
    else:
        variants.append(street_name.strip())
    
    # Clean up any empty strings
    variants = [v for v in variants if v]
    
    return variants

# Create the JSON structure for all target streets
simple_day_data = {}
streets_not_found = []

for street in target_streets:
    print(f"\nProcessing: {street}")
    
    # Get all possible street name variations for this entry
    street_variants = get_street_variants(street)
    print(f"  Searching for variants: {street_variants}")
    
    # Combine data from all street variants
    combined_data = pd.DataFrame()
    found_variants = []
    
    for variant in street_variants:
        # Find matching streets (using contains for partial matches)
        if isinstance(variant, str):
            # Use regex to match whole words or partial matches
            variant_data = df[df['road_name'].str.contains(variant, case=False, na=False, regex=False)]
            if len(variant_data) > 0:
                print(f"    Found {len(variant_data)} records for '{variant}'")
                combined_data = pd.concat([combined_data, variant_data])
                found_variants.append(variant)
            else:
                print(f"    No records found for '{variant}'")
    
    # Remove duplicates if any street appears in multiple variants
    if len(combined_data) > 0:
        combined_data = combined_data.drop_duplicates()
    
    # If no data found, add to not found list
    if len(combined_data) == 0:
        streets_not_found.append(street)
        print(f"  WARNING: No data found for any variant of '{street}'")
    
    # Calculate day totals - using 'daily_cyclists' column
    day_totals = {}
    for day in days_order:
        if len(combined_data) > 0:
            day_data = combined_data[combined_data['day_of_week'] == day]
            # Check if 'daily_cyclists' column exists
            if 'daily_cyclists' in day_data.columns:
                day_total = day_data['daily_cyclists'].sum()
                day_totals[day] = int(day_total)
            else:
                print(f"    Warning: 'daily_cyclists' column not found for {street}")
                day_totals[day] = 0
        else:
            day_totals[day] = 0
    
    simple_day_data[street] = {
        'day_totals': day_totals,
        'total_cyclists': sum(day_totals.values()),
        'variants_found': found_variants
    }

# Save to JSON file
with open(output_file, 'w') as f:
    json.dump(simple_day_data, f, indent=2)

print(f"\n{'='*60}")
print("Analysis complete!")
print(f"Output file: {output_file}")
print(f"Total streets processed: {len(simple_day_data)}")

if streets_not_found:
    print(f"\nStreets with NO data found ({len(streets_not_found)}):")
    for street in streets_not_found:
        print(f"  - {street}")
else:
    print("\nAll streets had some data found!")

print(f"\nTop 10 streets by total cyclists:")
# Sort streets by total cyclists
sorted_streets = sorted(simple_day_data.items(), key=lambda x: x[1]['total_cyclists'], reverse=True)
for i, (street, data) in enumerate(sorted_streets[:10]):
    print(f"  {i+1}. {street}: {data['total_cyclists']} cyclists")

# Show file size
if os.path.exists(output_file):
    file_size = os.path.getsize(output_file)
    print(f"\nFile size: {file_size / 1024:.2f} KB")