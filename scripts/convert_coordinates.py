#!/usr/bin/env python3

import re
import pandas as pd

# A helper function to parse a DMS string like "58°07'35,6\"" into decimal degrees
def parse_dms(dms_str: str) -> float:
    """
    Parse a DMS (degree/minute/second) string with potential comma decimal
    and return decimal degrees as a float.
    Assumes northern latitudes and eastern longitudes (positive coords).
    Example input: '58°07'35,6"'
    """
    # Replace comma with dot for consistency
    dms_str = dms_str.replace(',', '.')
    # Regex to capture degrees, minutes, and seconds
    pattern = r"(\d+)°(\d+)'([\d.]+)\""
    match = re.search(pattern, dms_str.strip())
    if not match:
        raise ValueError(f"Invalid DMS format: {dms_str}")

    deg = float(match.group(1))
    mins = float(match.group(2))
    secs = float(match.group(3))

    # Convert to decimal degrees
    decimal_degrees = deg + mins / 60 + secs / 3600
    return decimal_degrees

def main():
    # Input file path
    input_file = "/home/maakler/University-of-Tartu/Algoritmika/estonia_bike_route/scripts/cities_dms.txt"  # Ensure this file exists in the same directory or provide the full path

    # Read data from the .txt file
    print(f"Reading city data from: {input_file}")
    city_data = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            # Each line is expected to have CityName \t LatitudeDMS \t LongitudeDMS
            parts = line.strip().split("\t")
            if len(parts) != 3:
                print(f"Skipping invalid line: {line.strip()}")
                continue
            city, lat_dms, lon_dms = parts
            city_data.append((city, lat_dms, lon_dms))

    # Convert to decimal degrees
    print("Converting coordinates to decimal degrees...")
    converted_data = []
    for city, lat_dms, lon_dms in city_data:
        try:
            lat_dd = parse_dms(lat_dms)
            lon_dd = parse_dms(lon_dms)
            converted_data.append({
                "City": city,
                "Latitude": lat_dd,
                "Longitude": lon_dd
            })
        except ValueError as e:
            print(f"Error parsing DMS for city {city}: {e}")

    # Create a DataFrame
    df = pd.DataFrame(converted_data, columns=["City", "Latitude", "Longitude"])

    # Save to CSV
    output_file = "cities.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"Converted data saved to: {output_file}")

if __name__ == "__main__":
    main()
