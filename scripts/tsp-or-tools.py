from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import pandas as pd


def create_data_model():
    """
    Returns a data model containing:
      - The distance matrix
      - The list of city names
      - The index for the start city (Tartu)
      - The index for the end city (Tallinn)
    """
    # Load distance matrix from a CSV
    dist_df = pd.read_csv("distance_matrix.csv", index_col=0)

    # City names and distance matrix
    city_names = list(dist_df.index)
    distance_matrix = dist_df.values.tolist()

    # Identify start and end city indices
    start_index = city_names.index("Tartu")
    end_index = city_names.index("Tallinn")

    return {
        "distance_matrix": distance_matrix,
        "city_names": city_names,
        "start_index": start_index,
        "end_index": end_index,
    }


def main():
    # Create the data model
    data = create_data_model()
    distance_matrix = data["distance_matrix"]
    city_names = data["city_names"]
    start_index = data["start_index"]
    end_index = data["end_index"]

    # Number of cities
    num_cities = len(distance_matrix)

    # Create the routing index manager
    # The manager handles the mapping between city indices and internal indices.
    manager = pywrapcp.RoutingIndexManager(num_cities, 1, start_index)

    # Create the routing model
    routing = pywrapcp.RoutingModel(manager)

    # Define cost of each arc using the distance callback
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Set the cost of travel
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add a constraint to fix the end node
    # Force the last node of the route to be the specified end_index
    routing.AddDisjunction([manager.NodeToIndex(end_index)], 0)

    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Extract the solution if found
    if solution:
        print(f"Objective (Total Distance): {solution.ObjectiveValue()} meters")
        index = routing.Start(0)  # Start at the first node
        route = []
        while not routing.IsEnd(index):
            route.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))  # Add the end node

        # Convert route to city names
        route_cities = [city_names[node] for node in route]
        print("Route:", " -> ".join(route_cities))
    else:
        print("No solution found!")


if __name__ == "__main__":
    main()
