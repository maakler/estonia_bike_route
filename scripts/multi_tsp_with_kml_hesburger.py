#!/usr/bin/env python3
"""
multi_tsp_with_kml.py

Extends your multi_tsp_solutions.py to:
1) Solve TSP for three routes (Tartu->Tartu, Tartu->Tallinn, city[0]->city[0]).
2) Generate a KML file for each route automatically.

Requirements:
  - pip install ortools pandas
  - You have:
    - distance_matrix.csv: a square matrix of distances with city names in rows/columns
    - city_coords.csv: a file mapping City -> Latitude, Longitude
"""

import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ----------------------------
# 1) READ CITY -> LAT/LON
# ----------------------------
def read_city_coordinates(csv_file):
    """
    Reads city_coords.csv with columns: City, Latitude, Longitude
    Returns a dict: { "Tartu": (58.377, 26.729), "Tallinn": (59.4369, 24.7535), ... }
    """
    df = pd.read_csv(csv_file)
    city_dict = {}
    for i, row in df.iterrows():
        name = str(row["Restoran"]).strip()
        lat = float(row["Latitude"])
        lon = float(row["Longitude"])
        city_dict[name] = (lat, lon)
    return city_dict

# ----------------------------
# 2) READ DISTANCE MATRIX
# ----------------------------
def read_distance_matrix(csv_file):
    """
    Reads a distance matrix CSV (with city names as index/columns) into:
    - a 2D list (matrix)
    - a list of city names (index order)
    """
    df = pd.read_csv(csv_file, index_col=0)
    # Convert to a 2D list of floats (or ints)
    matrix = df.values.tolist()
    # Extract city names from the DataFrame index
    city_names = df.index.tolist()
    return matrix, city_names

# ----------------------------
# 3) TSP SOLVER
# ----------------------------
def solve_tsp(distance_matrix, start_index, end_index=None):
    """
    Solves TSP using OR-Tools, with an optional fixed end index.
    :param distance_matrix: 2D list of distances.
    :param start_index: int, the city index in matrix to start from.
    :param end_index: int or None, the city index to end at (None => same as start).
    :return: (route_indices, total_distance)
    """
    num_cities = len(distance_matrix)

    # If end_index is None => single-vehicle route that returns to start
    if end_index is None:
        manager = pywrapcp.RoutingIndexManager(num_cities, 1, start_index)
    else:
        manager = pywrapcp.RoutingIndexManager(
            num_cities, 1, [start_index], [end_index]
        )

    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return int(distance_matrix[from_node][to_node])

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    # Basic search parameters
    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = 300 # 10min

    solution = routing.SolveWithParameters(search_params)
    if solution:
        # Reconstruct route
        index = routing.Start(0)
        route_indices = []
        while not routing.IsEnd(index):
            route_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route_indices.append(manager.IndexToNode(index))  # add end city
        total_distance = solution.ObjectiveValue()
        return route_indices, total_distance
    else:
        return None, None

# ----------------------------
# 4) KML GENERATION
# ----------------------------
def generate_kml(route_city_names, city_coords, output_file, route_label="My Route"):
    """
    Generates a KML file with Placemarks for each city in the route
    and a LineString connecting them in order.

    :param route_city_names: list of city names in the order of the route
    :param city_coords: dict mapping city_name -> (lat, lon)
    :param output_file: path to output .kml file
    :param route_label: Name/description for the route
    """
    # We'll build a string representing KML structure
    # Note: KML uses lon,lat order inside <coordinates> by standard
    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>{}</name>
""".format(route_label)

    kml_footer = """
</Document>
</kml>
"""

    placemarks_str = ""
    coords_list = []  # store (lon, lat) for the linestring
    for city in route_city_names:
        if city not in city_coords:
            # If city coords not found, skip or raise an error
            print(f"Warning: {city} not found in city_coords, skipping in KML.")
            continue
        lat, lon = city_coords[city]  # lat,lon
        coords_list.append((lon, lat))
        # Create a Placemark
        placemark = f"""
    <Placemark>
      <name>{city}</name>
      <Point>
        <coordinates>{lon},{lat},0</coordinates>
      </Point>
    </Placemark>
"""
        placemarks_str += placemark

    # Build the LineString
    # We need "lon,lat,alt" for each point, joined by spaces
    linestring_coords = " ".join([f"{lon},{lat},0" for (lon, lat) in coords_list])
    linestring_placemark = f"""
    <Placemark>
      <name>{route_label} Path</name>
      <Style>
        <LineStyle>
          <color>ff0000ff</color> <!-- red line in ABGR format -->
          <width>3</width>
        </LineStyle>
      </Style>
      <LineString>
        <tessellate>1</tessellate>
        <coordinates>
          {linestring_coords}
        </coordinates>
      </LineString>
    </Placemark>
"""

    # Combine everything
    kml_content = kml_header + placemarks_str + linestring_placemark + kml_footer

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(kml_content)

    print(f"KML saved to {output_file}")

# ----------------------------
# 5) MAIN EXECUTION
# ----------------------------
def main():
    # Load the distance matrix
    dist_matrix, city_names = read_distance_matrix("hesburger_distance_matrix.csv")

    # Load city -> (lat, lon)
    city_coords = read_city_coordinates("data/hesburger_coords.csv")

    # Indices for Tartu & Tallinn
    try:
        tartu_idx = city_names.index("Hesburger Tartu Vabaduse")
    except ValueError:
        print("Error: 'Hesburger Tartu Vabaduse' not in city_names!")
        return
    try:
        tallinn_idx = city_names.index("Hesburger Tallinn Solaris Keskus")
    except ValueError:
        print("Error: 'Hesburger Tallinn Solaris Keskus' not in city_names!")
        return

    # 1) Tartu -> Tartu
    route_indices_tt, cost_tt = solve_tsp(dist_matrix, tartu_idx, None)
    if route_indices_tt:
        route_cities_tt = [city_names[i] for i in route_indices_tt]
        print("=== TSP: Tartu -> Tartu ===")
        print(f"Objective Distance: {cost_tt}")
        print("Route:", " -> ".join(route_cities_tt))

        # Create a KML for this route
        generate_kml(
            route_city_names=route_cities_tt,
            city_coords=city_coords,
            output_file="Vabaduse_Vabaduse.kml",
            route_label="Vabaduse -> Vabaduse"
        )

    # 2) Tartu -> Tallinn
    route_indices_tall, cost_tall = solve_tsp(dist_matrix, tartu_idx, tallinn_idx)
    if route_indices_tall:
        route_cities_tall = [city_names[i] for i in route_indices_tall]
        print("\n=== TSP: Tartu -> Tallinn ===")
        print(f"Objective Distance: {cost_tall}")
        print("Route:", " -> ".join(route_cities_tall))

        # Create a KML for this route
        generate_kml(
            route_city_names=route_cities_tall,
            city_coords=city_coords,
            output_file="Vabaduse_Solaris.kml",
            route_label="Vabaduse -> Solaris"
        )

    # 3) city[0] -> city[0]
    # route_indices_0, cost_0 = solve_tsp(dist_matrix, 0, None)
    # if route_indices_0:
    #     route_cities_0 = [city_names[i] for i in route_indices_0]
    #     print("\n=== TSP: city[0] -> city[0] ===")
    #     print(f"Objective Distance: {cost_0}")
    #     print("Route:", " -> ".join(route_cities_0))

    #     # Create a KML for this route
    #     start_city = city_names[0]
    #     generate_kml(
    #         route_city_names=route_cities_0,
    #         city_coords=city_coords,
    #         output_file=f"{start_city}_{start_city}.kml",
    #         route_label=f"{start_city} -> {start_city}"
    #     )

if __name__ == "__main__":
    main()
