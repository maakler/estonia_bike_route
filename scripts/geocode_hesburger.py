#!/usr/bin/env python3
"""
geocode_hesburger.py

Takes a CSV with columns: Name,City,Address
Queries the OpenRouteService Geocoding API to find latitude/longitude for each address.
Outputs a CSV with columns: Name,City,Address,Latitude,Longitude
"""

import pandas as pd
import requests
import urllib.parse

# Replace with your ORS API key
API_KEY = "5b3ce3597851110001cf6248931d189b3a424b0a90b621b4003aeecb"

# ORS Geocode endpoint
GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"

def geocode_address(address):
    """
    Queries ORS geocoding for the given address, returns (lat, lon) or (None, None) if not found.
    """
    params = {
        "api_key": API_KEY,
        "text": address,
        "size": 1,         # Return only 1 best match
        "boundary.country": "EE"  # Restrict search to Estonia if you wish
    }
    try:
        r = requests.get(GEOCODE_URL, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            if len(features) > 0:
                # The first feature is presumably the best match
                coords = features[0]["geometry"]["coordinates"]
                lon, lat = coords[0], coords[1]
                return (lat, lon)
        else:
            print(f"Geocoding API error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Request exception for address '{address}': {e}")
    return (None, None)

def main():
    input_csv = "data/hesburger_locations.csv"
    output_csv = "hesburger_coords.csv"

    # 1. Read data
    df = pd.read_csv(input_csv)
    # Ensure columns: Name, City, Address
    # If your CSV has different column names, adjust accordingly.

    # 2. Geocode each row
    latitudes = []
    longitudes = []

    for i, row in df.iterrows():
        name = row["Restoran"]
        city = row["Asula"]
        address = row["Aadress"]
        
        # Build a full address string. You might combine city+address if needed:
        full_address = f"{address}, {city}, Estonia"

        print(f"Geocoding: {full_address}")
        lat, lon = geocode_address(full_address)
        latitudes.append(lat)
        longitudes.append(lon)

    # 3. Append results to DataFrame and save
    df["Latitude"] = latitudes
    df["Longitude"] = longitudes

    # Filter out rows where lat/lon was not found if you want
    # df = df.dropna(subset=["Latitude", "Longitude"])

    df.to_csv(output_csv, index=False)
    print(f"\nSaved geocoded data to: {output_csv}")

if __name__ == "__main__":
    main()
