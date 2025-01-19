#!/usr/bin/env python3
"""
inspect_data.py

Script to iterate over each .shp file in the data folder and print attributes.
"""

import os
import geopandas as gpd

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    # Recursively look for shapefiles
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.lower().endswith(".shp"):
                shp_path = os.path.join(root, file)
                print("="*80)
                print(f"Inspecting: {shp_path}")
                try:
                    gdf = gpd.read_file(shp_path)
                    print("Columns:", gdf.columns.tolist())
                    print(gdf.head(3))  # show first 3 rows
                except Exception as e:
                    print(f"Could not read {shp_path}. Error: {e}")
                print("="*80)

if __name__ == "__main__":
    main()
