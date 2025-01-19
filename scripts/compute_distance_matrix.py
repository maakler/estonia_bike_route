#!/usr/bin/env python3
"""
ors_matrix_api.py

Reads a CSV of cities with lat/lon, queries the OpenRouteService Matrix API,
and outputs distance and duration matrices as CSVs.

Note: Replace "YOUR_API_KEY" with your actual ORS API key.
"""

import csv
import requests
import pandas as pd

# Replace with your ORS API key
API_KEY = "5b3ce3597851110001cf6248931d189b3a424b0a90b621b4003aeecb"

# ORS Matrix endpoint
MATRIX_URL = "https://api.openrouteservice.org/v2/matrix"

# Profile can be "driving-car", "cycling-regular", "foot-walking", etc.
PROFILE = "driving-car"

def main():
    # 1. Read city data
    csv_file = "data/cities.csv"  # Adjust if needed
    city_data = pd.read_csv(csv_file)

    # We need coordinates in [lon, lat] format for ORS
    # city_data columns: City, Latitude, Longitude
    coords = []
    city_names = []
    
    for index, row in city_data.iterrows():
        city_names.append(row["City"].strip())
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        coords.append([lon, lat])  # ORS expects [lon, lat]

    # 2. Prepare the POST request body
    payload = {
        "locations": coords,
        "metrics": ["distance", "duration"],
        # 'units': "km"   # By default, distances come in meters. 
        # If you set units to "km", distances come in kilometers (ORS docs).
    }

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }

    # 3. Send the request
    print(f"Requesting matrix from ORS for {len(coords)} cities...")
    response = requests.post(f"{MATRIX_URL}/{PROFILE}", json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"ORS Matrix API error: {response.status_code}, {response.text}")

    result = response.json()

    # 4. Extract distances (meters) and durations (seconds)
    # result has keys "distances" and "durations", each is a 2D list
    distances = result.get("distances", [])
    durations = result.get("durations", [])

    # 5. Convert to DataFrame for easy CSV export
    dist_df = pd.DataFrame(distances, index=city_names, columns=city_names)
    dur_df = pd.DataFrame(durations, index=city_names, columns=city_names)

    # 6. Save to CSV
    dist_df.to_csv("distance_matrix.csv")
    dur_df.to_csv("duration_matrix.csv")

    print("Done! distance_matrix.csv and duration_matrix.csv have been created.")

if __name__ == "__main__":
    main()
