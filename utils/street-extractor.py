#!/usr/bin/env python3
"""
This script is used to extract Road segements from OSM data based on cyclist activity data.
These extracted roads are used to display road segments for Route Popularity map in Tab 3.
Trim OSM road geometries to cyclist activity corridors.
Processes street popularity data and cycling GPS data to identify active segments.
"""

print("Step 0: Starting script...")
print("Step 0.1: Importing libraries...")

import os

# Fix for pyproj CRSError: Set PROJ path explicitly using pyproj.datadir
try:
    import pyproj
    # This path was verified by utils/debug_pyproj.py
    pyproj_path = "/opt/anaconda3/envs/spinovate/share/proj"
    pyproj.datadir.set_data_dir(pyproj_path)
    print(f"DEBUG: Manually set pyproj data dir to {pyproj_path}")
except ImportError:
    pass

import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import linemerge, unary_union, split
from shapely import wkt
import numpy as np
print("Step 0.2: Libraries imported successfully.")

# ======================================================
# STEP 1: Load your datasets
# ======================================================
def main():
    print("Step 1: Loading datasets...")

    file_a = pd.read_csv("/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/tab3_routepopularity/dlr-route-popularity.csv")
    file_b = pd.read_parquet("/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/tab3_routepopularity/dublin-lights_v2.parquet", engine="fastparquet")
    print("Step 1.1: Datasets loaded. Populating GeoDataFrame...")
    
    # DEBUG: Print sample data
    print("\n=== DEBUG: Checking data ===")
    print(f"file_a (dlr-route-popularity.csv) has {len(file_a)} rows")
    print("First few rows of file_a:")
    print(file_a[["Street Name"]].head(10))
    
    print(f"\nfile_b (dublin-lights.parquet) has {len(file_b)} rows")
    if "road_name" in file_b.columns:
        print("Unique road names in file_b (first 20):")
        unique_roads = file_b["road_name"].dropna().unique()
        print(unique_roads[:20])
        print(f"Total unique road names: {len(unique_roads)}")
    else:
        print("Column 'road_name' not found in file_b")
        print("Available columns:", file_b.columns.tolist())

    # Clean names
    file_a["street_name_clean"] = file_a["Street Name"].str.lower().str.strip()
    file_b["road_name_clean"] = file_b["road_name"].str.lower().str.strip()

    # Convert coordinates into GeoDataFrame
    gdf_points = gpd.GeoDataFrame(
        file_b,
        geometry=gpd.points_from_xy(file_b.longitude, file_b.latitude),
        crs="EPSG:4326"
    )

    # ======================================================
    # NEW STEP 1.5: Download Dublin Map ONCE
    # ======================================================
    print("\nStep 1.5: Getting Dublin OSM Grid...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    graph_filename = os.path.join(script_dir, "dublin_graph.graphml")
    
    print(f"  Looking for cached graph at: {graph_filename}")

    try:
        if os.path.exists(graph_filename):
            print(f"  Loading cached graph from {graph_filename}...")
            graph = ox.load_graphml(graph_filename)
            print("  ✅ Graph loaded from cache")
        else:
            print("  Graph file not found. Downloading from OSM...")
            print("  Downloading graph from OSM (Radius: 15km, Type: all)...")
            center_point = (53.34, -6.26)  # Dublin city centre
            radius_m = 15000  # 15 km radius covers DLR & City comfortably
            
            graph = ox.graph_from_point(center_point, dist=radius_m, network_type="all")
            
            print(f"  Saving graph to {graph_filename} for future use...")
            ox.save_graphml(graph, graph_filename)
            print("  ✅ Graph downloaded and saved")

        print("  Converting graph to GeoDataFrame...")
        gdf_edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)

        # flatten list columns
        for col in ["name", "ref"]:
            if col in gdf_edges.columns:
                 gdf_edges[col] = gdf_edges[col].apply(
                    lambda v: ", ".join(v) if isinstance(v, list) else v
                )

        print(f"  ✅ Map data prepared successfully. Found {len(gdf_edges)} road segments.")

    except Exception as e:
        print(f"CRITICAL ERROR: Could not prepare OSM data: {e}")
        return

    # ======================================================
    # STEP 2: Define function to get OSM road geometry
    # ======================================================

    def get_street_geometry(street_name, all_edges):
        """
        Fetch OSM road geometry from the pre-loaded edges.
        """
        try:
            # DEBUG: Show what we're searching for
            # print(f"  Searching for: '{street_name}'")
            
            # match by name or ref
            matches = all_edges[
                (all_edges["name"].str.lower().str.contains(street_name, na=False))
                | (all_edges["ref"].str.lower().str.contains(street_name, na=False))
            ]

            # explicit fallback for Kill Lane / R830
            if matches.empty and "kill lane" in street_name:
                matches = all_edges[all_edges["ref"].str.lower().str.contains("r830", na=False)]

            if matches.empty:
                print(f"  ⚠️ No OSM match found for: {street_name}")
                # DEBUG: Try to find partial matches
                partial_matches = all_edges[
                    all_edges["name"].str.lower().str.contains(street_name.split()[0] if len(street_name.split()) > 0 else street_name, na=False)
                ]
                if len(partial_matches) > 0:
                    print(f"  ℹ️ But found {len(partial_matches)} partial matches for first word")
                return None
            
            print(f"  ✅ Found {len(matches)} OSM segments for: {street_name}")
            
            # DEBUG: Show sample of matched road names
            if "name" in matches.columns:
                unique_names = matches["name"].dropna().unique()
                print(f"  ℹ️ Matched OSM names: {unique_names[:5]}")  # Show first 5

            merged = linemerge(unary_union(matches.geometry))
            return merged

        except Exception as e:
            print(f"  Error fetching geometry for {street_name}: {e}")
            return None


    # ======================================================
    # STEP 3: Trim road geometry to cyclist coverage
    # ======================================================

    def trim_geometry_to_points(road_geom, points_gdf, buffer_m=25):
        """
        Trims a road geometry (LineString or MultiLineString) to only the
        sections that have cyclist activity nearby. Returns a merged
        LineString or MultiLineString in EPSG:4326.
        """
        # Convert to projected CRS for accurate buffering
        road_gdf = gpd.GeoDataFrame(geometry=[road_geom], crs="EPSG:4326").to_crs(epsg=3857)
        points_proj = points_gdf.to_crs(epsg=3857)

        # Buffer around cyclist points to represent the active corridor
        buffer_union = unary_union(points_proj.buffer(buffer_m))

        # Intersect the road with buffered corridor
        clipped = road_gdf.intersection(buffer_union)
        clipped = clipped.explode(index_parts=False).reset_index(drop=True)

        # Drop empty intersections
        clipped = clipped[~clipped.is_empty]
        if clipped.empty:
            print(f"    No intersection with cyclist points after buffering")
            return None

        # Simplify to valid lines only
        valid_geoms = [geom for geom in clipped.geometry if geom.is_valid and geom.length > 0]
        if not valid_geoms:
            print(f"    No valid geometries after clipping")
            return None

        # Merge if possible, but handle single LineStrings safely
        try:
            merged = linemerge(unary_union(valid_geoms))
        except Exception:
            merged = unary_union(valid_geoms)

        # Convert back to WGS84
        merged_gdf = gpd.GeoDataFrame(geometry=[merged], crs="EPSG:3857").to_crs(epsg=4326)
        return merged_gdf.iloc[0].geometry


    # ======================================================
    # STEP 4: Process each street
    # ======================================================
    print(f"\nStep 4: Processing {len(file_a)} streets...")
    print("=" * 50)

    final_segments = []

    for idx, row in file_a.iterrows():
        original_name = row['Street Name']
        street_name = row["street_name_clean"]
        print(f"\nStep 4.{idx+1}: Processing: {original_name}")
        print(f"  Clean name: '{street_name}'")
        
        # DEBUG: Check if this street name exists in file_b
        matching_points = gdf_points[gdf_points["road_name_clean"] == street_name]
        if len(matching_points) == 0:
            # Try partial matching
            print(f"  DEBUG: No exact match for '{street_name}' in cyclist data")
            print(f"  DEBUG: Trying to find similar names...")
            
            # Try to find any road name containing parts of this street name
            name_parts = street_name.split()
            for part in name_parts:
                if len(part) > 3:  # Only search for significant parts
                    partial_matches = gdf_points[gdf_points["road_name_clean"].str.contains(part, na=False)]
                    if len(partial_matches) > 0:
                        print(f"  DEBUG: Found {len(partial_matches)} points with '{part}' in road_name")
                        print(f"  DEBUG: Sample road names: {partial_matches['road_name'].unique()[:3]}")

        # Handle multi-road entries
        # First try to split by common separators
        separators = ['&', '/', 'and', ',', ';']
        parts = [street_name]
        
        for sep in separators:
            new_parts = []
            for part in parts:
                if sep in part:
                    new_parts.extend([p.strip() for p in part.split(sep)])
                else:
                    new_parts.append(part)
            parts = new_parts
        
        print(f"  Split into {len(parts)} parts: {parts}")

        all_parts = []
        for part_idx, part in enumerate(parts):
            if not part or part.strip() == "":
                continue
                
            print(f"\n  Part {part_idx+1}/{len(parts)}: '{part}'")
            
            # Pass the pre-loaded edges here
            osm_geom = get_street_geometry(part, gdf_edges)
            if osm_geom is None:
                continue

            # Filter cyclist points for this road
            # Try different matching strategies
            subset_points = gdf_points[gdf_points["road_name_clean"].str.contains(part, na=False)]
            
            # If still empty, try more flexible matching
            if subset_points.empty:
                # Try matching any word in the part
                words = part.split()
                for word in words:
                    if len(word) > 3:  # Only meaningful words
                        word_points = gdf_points[gdf_points["road_name_clean"].str.contains(word, na=False)]
                        if not word_points.empty:
                            subset_points = word_points
                            print(f"    Found {len(subset_points)} points using word '{word}'")
                            break
            
            print(f"    Found {len(subset_points)} cyclist points for this road")
            
            if subset_points.empty:
                print(f"    ⚠️ No cyclist data found for '{part}'")
                # DEBUG: Show what road names are actually in the data
                sample_roads = gdf_points["road_name"].dropna().unique()[:10]
                print(f"    ℹ️ Sample road names in cyclist data: {sample_roads}")
                continue

            trimmed = trim_geometry_to_points(osm_geom, subset_points)
            if trimmed is not None:
                print(f"    ✅ Successfully trimmed geometry for '{part}'")
                all_parts.append(trimmed)
            else:
                print(f"    ⚠️ Could not trim geometry for '{part}'")

        if not all_parts:
            print(f"  ⚠️ No valid trimmed geometries for {original_name}")
            continue

        # Merge all parts for this street
        try:
            merged_trimmed = unary_union(all_parts)
            final_segments.append({
                "street_name": original_name,
                "original_clean_name": street_name,
                "geometry": merged_trimmed
            })
            print(f"  ✅ Added {original_name} to final segments")
        except Exception as e:
            print(f"  Error merging parts for {original_name}: {e}")

    # ======================================================
    # STEP 5: Export to GeoJSON
    # ======================================================
    print("\n" + "=" * 50)
    if not final_segments:
        print("\n⚠️ WARNING: No road segments were successfully extracted!")
        print("\nPossible reasons:")
        print("1. Street names in dlr-route-popularity.csv don't match road names in dublin-lights.parquet")
        print("2. No cyclist GPS points near these roads")
        print("3. The dublin-lights.parquet file might not have data for these specific roads")
        print("4. There might be data quality issues (missing road names in GPS data)")
        print("\nSuggestions:")
        print("1. Check the road_name column in dublin-lights.parquet")
        print("2. Verify the Street Name column in dlr-route-popularity.csv")
        print("3. Consider using spatial matching instead of name matching")
        print("\nCreating empty GeoDataFrame...")
        
        # Create empty GeoDataFrame with correct structure
        gdf_final = gpd.GeoDataFrame(columns=["street_name", "original_clean_name", "geometry"], crs="EPSG:4326")
    else:
        print(f"\n✅ Successfully extracted {len(final_segments)} road segments")
        gdf_final = gpd.GeoDataFrame(final_segments, crs="EPSG:4326")
    
    # Export to file in the same directory as the script
    output_file = os.path.join(script_dir, "trimmed_active_segments.geojson")
    gdf_final.to_file(output_file, driver="GeoJSON")
    print(f"✅ GeoDataFrame saved to '{output_file}'")
    print(f"   Contains {len(gdf_final)} features")

    # Print summary
    print("\n=== PROCESSING SUMMARY ===")
    print(f"Total streets in input: {len(file_a)}")
    print(f"Successfully processed: {len(final_segments)}")
    print(f"Failed to process: {len(file_a) - len(final_segments)}")


if __name__ == "__main__":
    main()