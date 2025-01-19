#!/usr/bin/env python3
"""
multi_tsp_with_gpx.py

1) Solve TSP for two routes (Tartu->Tartu, Tartu->Tallinn) using OR-Tools.
2) Generate a GPX file for each route automatically (suitable for Strava upload).

You'll need:
  - distance_matrix.csv (a square matrix of distances with city names in rows/columns)
  - city_coords.csv (file mapping City -> Latitude, Longitude)
  - OR-Tools installed: pip install ortools pandas
  - A valid set of city names in 'city_coords.csv' matching those in 'distance_matrix.csv'
"""

import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ----------------------------
# 1) READ CITY -> LAT/LON
# ----------------------------
def read_city_coordinates(csv_file):
    """
    Reads city_coords.csv with columns: "Restoran", "Latitude", "Longitude"
    Returns a dict: { "Hesburger Tartu Vabaduse": (58.377, 26.729), ... }
    """
    df = pd.read_csv(csv_file)
    city_dict = {}
    for i, row in df.iterrows():
        name = str(row["City"]).strip()
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        city_dict[name] = (lat, lon)
    return city_dict

# ----------------------------
# 2) READ DISTANCE MATRIX
# ----------------------------
def read_distance_matrix(csv_file):
    """
    Reads a distance matrix CSV (with city names as index/columns).
    Returns:
      - matrix: 2D list (distance_matrix[row][col])
      - city_names: list of city names in the index order
    """
    df = pd.read_csv(csv_file, index_col=0)
    matrix = df.values.tolist()
    city_names = df.index.tolist()
    return matrix, city_names

# ----------------------------
# 3) TSP SOLVER
# ----------------------------
def solve_tsp(distance_matrix, start_index, end_index=None):
    """
    Solves TSP using OR-Tools, with an optional fixed end index.
    :param distance_matrix: NxN list of distances.
    :param start_index: index of the start city in the city_names list
    :param end_index: index of the end city, or None if round trip
    :return: (route_indices, total_distance)
    """
    num_cities = len(distance_matrix)

    # Create manager
    if end_index is None:
        # start/end same
        manager = pywrapcp.RoutingIndexManager(num_cities, 1, start_index)
    else:
        # fixed start & end
        manager = pywrapcp.RoutingIndexManager(num_cities, 1, [start_index], [end_index])

    # Create routing model
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return int(distance_matrix[from_node][to_node])

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    # Basic search params
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 900  # up to 5 minutes

    # Solve
    solution = routing.SolveWithParameters(search_params)
    if solution:
        # Rebuild route
        index = routing.Start(0)
        route_indices = []
        while not routing.IsEnd(index):
            route_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route_indices.append(manager.IndexToNode(index))
        total_distance = solution.ObjectiveValue()
        return route_indices, total_distance
    else:
        return None, None

# ----------------------------
# 4) GPX GENERATION
# ----------------------------
def generate_gpx(route_city_names, city_coords, output_file, route_label="My Route"):
    """
    Generates a GPX file with a <trk> and <trkseg> for Strava.
    route_city_names: [ city1, city2, ... ] in the exact visiting order
    city_coords: dict { "CityName": (lat, lon), ... }
    output_file: "my_route.gpx"
    route_label: e.g. "Hesburger Tartu -> Tallinn"
    """
    # GPX header
    gpx_header = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<gpx version="1.1" creator="MyTSPApp" xmlns="http://www.topografix.com/GPX/1/1">
  <metadata>
    <name>{route_label}</name>
    <author>My TSP Solver</author>
  </metadata>
  <trk>
    <name>{route_label}</name>
    <trkseg>
"""

    # GPX footer
    gpx_footer = """    </trkseg>
  </trk>
</gpx>
"""

    trkpts_str = ""
    for city in route_city_names:
        if city not in city_coords:
            print(f"Warning: {city} missing in city_coords; skipping in GPX.")
            continue
        lat, lon = city_coords[city]
        # <trkpt lat=".." lon=".."><name>CityName</name></trkpt>
        trkpts_str += f"""      <trkpt lat="{lat}" lon="{lon}">
        <name>{city}</name>
      </trkpt>
"""

    gpx_content = gpx_header + trkpts_str + gpx_footer

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(gpx_content)

    print(f"GPX saved to {output_file}")

# ----------------------------
# 5) MAIN EXECUTION
# ----------------------------
def main():
    # 1. Load the distance matrix
    dist_matrix, city_names = read_distance_matrix("distance_matrix.csv")

    # 2. Load city -> (lat, lon)
    city_coords = read_city_coordinates("data/cities.csv")

    # We'll assume you want to start from "Hesburger Tartu Vabaduse"...
    try:
        tartu_idx = city_names.index("Tartu")
    except ValueError:
        print("Error: 'Hesburger Tartu Vabaduse' not in city_names!")
        return

    # ...and end at "Hesburger Tallinn Solaris Keskus"
    try:
        tallinn_idx = city_names.index("Tallinn")
    except ValueError:
        print("Error: 'Hesburger Tallinn Solaris Keskus' not in city_names!")
        return


    route_indices_tall, cost_tall = solve_tsp(dist_matrix, tartu_idx, tallinn_idx)
    if route_indices_tall:
        route_cities_tall = [city_names[i] for i in route_indices_tall]
        print("\n=== TSP: Tartu -> Tallinn ===")
        print(f"Objective Distance: {cost_tall}")
        print("Route:", " -> ".join(route_cities_tall))
        # Generate GPX
        generate_gpx(
            route_city_names=route_cities_tall,
            city_coords=city_coords,
            output_file="Tartu_Tallinn.gpx",
            route_label="Tartu -> Tallinn"
        )

if __name__ == "__main__":
    main()
