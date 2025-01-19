#!/usr/bin/env python3
"""
ors_matrix_api_chunked.py

Splits the ORS Matrix requests into chunks so as not to exceed
the 3,500-route server limit in each request.

Example logic:
- Suppose you have N=81 locations (81x81=6561 routes > 3500).
- chunk_size = floor(3500 / 81) = 43
- We'll do 2 calls:
  - sources = [0..42], destinations = [0..80]
  - sources = [43..80], destinations = [0..80]
- Then merge results to form a full 81x81 matrix.

Adjust 'PROFILE' and 'API_KEY' to your needs.
"""

import math
import requests
import pandas as pd

API_KEY = "5b3ce3597851110001cf6248931d189b3a424b0a90b621b4003aeecb"  # put your real ORS key here
MATRIX_URL = "https://api.openrouteservice.org/v2/matrix"
PROFILE = "foot-walking"  # or "driving-car", "cycling-regular", etc.

def main():
    # 1. Load your CSV (city, lat, lon)
    csv_file = "data/hesburger_coords.csv"
    df = pd.read_csv(csv_file)

    # Build the 'locations' list [ [lon, lat], ... ]
    coords = []
    city_names = []
    for i, row in df.iterrows():
        city = str(row["Restoran"]).strip()
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        coords.append([lon, lat])  # ORS expects [lon, lat]
        city_names.append(city)

    N = len(coords)
    print(f"Total points: {N}")

    # 2. Determine chunk size so chunk_size*N <= 3500
    #    This ensures each sub-request doesn't exceed the 3500-route limit.
    chunk_size = math.floor(3500 / N)
    if chunk_size < 1:
        # If chunk_size=0, then N is too large for this simple approach
        # We would need to chunk destinations as well. 
        raise ValueError(
            f"Too many points ({N}) to even have 1 row in chunk. "
            "Try chunking columns as well or reduce your dataset."
        )

    print(f"Using chunk_size={chunk_size}. Each sub-request = {chunk_size} * {N} = {chunk_size*N} routes.")

    # We'll prepare empty 2D arrays for distances & durations, size NxN
    dist_matrix = [[0.0]*N for _ in range(N)]
    dur_matrix = [[0.0]*N for _ in range(N)]

    # 3. For each chunk of sources, call the API
    start_idx = 0
    while start_idx < N:
        end_idx = min(start_idx + chunk_size, N)
        chunk_length = end_idx - start_idx

        # Prepare the request payload
        # We specify the entire set of locations,
        # but limit "sources" to this chunk, and "destinations" to [all].
        payload = {
            "locations": coords,         # all points
            "metrics": ["distance","duration"],
            "sources": list(range(start_idx, end_idx)),  # chunk
            "destinations": list(range(N)),              # full
        }

        headers = {
            "Authorization": API_KEY,
            "Content-Type": "application/json"
        }

        print(f"Requesting matrix for sources={start_idx}..{end_idx-1} of {N} (size {chunk_length})")
        r = requests.post(f"{MATRIX_URL}/{PROFILE}", json=payload, headers=headers)
        if r.status_code != 200:
            raise Exception(
                f"ORS Matrix API error: {r.status_code}, {r.text}"
            )

        result = r.json()
        sub_dist = result["distances"]   # chunk_length x N
        sub_dur = result["durations"]    # chunk_length x N

        # 4. Merge sub-results into the main NxN arrays
        # sub_dist[i][j] is the distance from source (start_idx + i) to j
        for i in range(chunk_length):
            global_row = start_idx + i
            for j in range(N):
                dist_matrix[global_row][j] = sub_dist[i][j]
                dur_matrix[global_row][j] = sub_dur[i][j]

        # Advance chunk
        start_idx = end_idx

    print("All chunks processed. Building DataFrames...")

    # 5. Create pandas DataFrames for easier CSV output
    dist_df = pd.DataFrame(dist_matrix, index=city_names, columns=city_names)
    dur_df = pd.DataFrame(dur_matrix, index=city_names, columns=city_names)

    # 6. Save results
    dist_df.to_csv("hesburger_distance_matrix.csv")
    dur_df.to_csv("hesburger_duration_matrix.csv")
    print("Done! hesburger_distance_matrix.csv and hesburger_duration_matrix.csv created.")

if __name__ == "__main__":
    main()
