#!/usr/bin/env python3
"""
This script extracts weekly trends from metadata file.
The output would be used for Trend analysis line graph.
"""

import pandas as pd
import json
import sys
from pathlib import Path
from datetime import datetime
import os

# Define file paths
data_dir = "/Users/abhishekkumbhar/Documents/GitHub/DLR-dashboard/data/processed/tab3_routepopularity"
INPUT_FILE = os.path.join(data_dir, "street_trends_metadata_tab3.json")
OUTPUT_FILE = os.path.join(data_dir, "clean_street_trends.json")


def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    with input_path.open("r", encoding="utf-8") as f:
        metadata = json.load(f)

    clean = {}

    for street_name, street_data in metadata.items():
        weekly_data = street_data.get("weekly", [])

        cleaned_weekly = []
        for entry in weekly_data:
            if not isinstance(entry, dict):
                continue

            cleaned_weekly.append({
                "date": entry.get("date"),
                "popularity_score": entry.get("daily_popularity"),
                "cyclist_volume": entry.get("daily_cyclists"),
            })

        clean[street_name] = {
            "weekly": cleaned_weekly
        }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

    print(f"Wrote clean weekly trends to {output_path}")


if __name__ == "__main__":
    main()