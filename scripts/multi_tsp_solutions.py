#!/usr/bin/env python3
"""
multi_tsp_solutions.py

Demonstrate three ways of using Google OR-Tools for TSP with a given distance matrix:
1) Round trip Tartu->Tartu
2) Start in Tartu, end in Tallinn
3) A standard TSP cycle from city index 0 (could be any city you want in the CSV)

Make sure your distance_matrix.csv is properly labeled and non-zero where needed!
"""

import pandas as pd
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def read_distance_matrix(csv_file):
    """Reads a distance matrix CSV (with city names as index/columns) into a 2D list."""
    df = pd.read_csv(csv_file, index_col=0)
    # Convert to a 2D list of floats (or ints)
    matrix = df.values.tolist()
    # City names from the DataFrame index
    city_names = df.index.tolist()
    return matrix, city_names

def solve_tsp(distance_matrix, start_index, end_index=None):
    """
    Solves TSP using OR-Tools, with an optional fixed end index.
    :param distance_matrix: 2D list of distances.
    :param start_index: int, the city index in matrix to start from.
    :param end_index: int or None, the city index in matrix to end at (None => same as start).
    :return: (route_indices, total_distance)
    """
    # Number of cities
    num_cities = len(distance_matrix)

    # Create the index manager
    # OR-Tools has two main constructor patterns:
    #  1) For a single-vehicle route with only a start depot:
    #       manager = pywrapcp.RoutingIndexManager(num_cities, 1, start_index)
    #  2) For a single-vehicle route with start & end:
    #       manager = pywrapcp.RoutingIndexManager(num_cities, 1, [start], [end])
    #
    # We'll handle both below:
    if end_index is None:
        # Start & end at the same city
        manager = pywrapcp.RoutingIndexManager(num_cities, 1, start_index)
        force_end = False
    else:
        # Start at start_index, end at end_index
        manager = pywrapcp.RoutingIndexManager(
            num_cities, 
            1, 
            [start_index], 
            [end_index]
        )
        force_end = True

    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)

    # Register a transit callback for distances
    def distance_callback(from_idx, to_idx):
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        # Convert to int if your matrix is float
        return int(distance_matrix[from_node][to_node])

    transit_callback_idx = routing.RegisterTransitCallback(distance_callback)

    # Set cost (distance) of each edge
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_idx)

    # If using the single-depot constructor (start only),
    # we still need to tell it to return to start for TSP. OR-Tools does that by default for 1 vehicle.
    # If we want a fixed end, we've used the second constructor.

    # Setup search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        # Reconstruct route
        index = routing.Start(0)
        route_indices = []
        while not routing.IsEnd(index):
            route_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route_indices.append(manager.IndexToNode(index))  # add the end

        # Extract objective
        total_distance = solution.ObjectiveValue()
        return route_indices, total_distance
    else:
        return None, None

def main():
    # 1. Load the distance matrix
    dist_matrix, city_names = read_distance_matrix("distance_matrix.csv")

    # Check if Tartu and Tallinn exist in the city list
    # We'll handle them by name -> index
    try:
        tartu_index = city_names.index("Tartu")
    except ValueError:
        print("Error: 'Tartu' not found in the city list!")
        return
    try:
        tallinn_index = city_names.index("Tallinn")
    except ValueError:
        print("Error: 'Tallinn' not found in the city list!")
        return

    # ----------------------------
    # 2. Solve TSP: Tartu -> Tartu
    # ----------------------------
    route_indices_tt, cost_tt = solve_tsp(dist_matrix, tartu_index, end_index=None)
    if route_indices_tt is not None:
        route_cities_tt = [city_names[i] for i in route_indices_tt]
        print("=== TSP: Tartu -> Tartu ===")
        print(f"Objective Distance: {cost_tt}")
        print("Route:", " -> ".join(route_cities_tt))
    else:
        print("No solution found for Tartu->Tartu")

    # ----------------------------
    # 3. Solve TSP: Tartu -> Tallinn
    # ----------------------------
    route_indices_tall, cost_tall = solve_tsp(dist_matrix, tartu_index, end_index=tallinn_index)
    if route_indices_tall is not None:
        route_cities_tall = [city_names[i] for i in route_indices_tall]
        print("\n=== TSP: Tartu -> Tallinn ===")
        print(f"Objective Distance: {cost_tall}")
        print("Route:", " -> ".join(route_cities_tall))
    else:
        print("No solution found for Tartu->Tallinn")

    # ----------------------------
    # 4. Solve TSP: Minimal cycle from city[0] -> city[0]
    # (If you want "any city" start, this typically picks city 0 as the start.)
    # ----------------------------
    route_indices_0, cost_0 = solve_tsp(dist_matrix, start_index=0, end_index=None)
    if route_indices_0 is not None:
        route_cities_0 = [city_names[i] for i in route_indices_0]
        print("\n=== TSP: city[0] -> city[0] ===")
        print(f"Objective Distance: {cost_0}")
        print("Route:", " -> ".join(route_cities_0))
    else:
        print("No solution found for city[0]->city[0]")

if __name__ == "__main__":
    main()
