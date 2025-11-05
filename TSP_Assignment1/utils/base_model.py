"""
Base utility functions for TSP models
Contains common functionality used by all three TSP formulations
"""

import sys
import os
import math
from typing import Dict, Tuple, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    print("Error: gurobipy not found. Please install it with: pip install gurobipy")
    sys.exit(1)


def load_data() -> Tuple[Dict[str, Tuple[float, float]], List[str]]:
    """
    Load coordinate data from NorwayTSP_Data (1).py (original assignment format)
    
    Returns:
        Tuple of (coordinates_dict, city_names_list)
        coordinates_dict: {city_name: (x, y)}
        city_names_list: Ordered list of city names (City1, City2, ..., City103)
    """
    try:
        # Find the original data file in the parent directory
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_file = os.path.join(current_dir, "NorwayTSP_Data (1).py")
        
        if not os.path.exists(data_file):
            # Fallback: try data directory
            data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'NorwayTSP_Data.py')
            if os.path.exists(data_file):
                sys.path.append(os.path.dirname(data_file))
                from NorwayTSP_Data import NORWAY_COORDINATES
                cities = list(NORWAY_COORDINATES.keys())
                coords = NORWAY_COORDINATES
                return coords, cities
            else:
                raise FileNotFoundError(f"Could not find NorwayTSP_Data (1).py in {current_dir}")
        
        # Read and execute the original data file format
        with open(data_file, 'r', encoding='utf-8') as f:
            data_code = f.read()
        
        # Execute in a namespace to get xcoord and ycoord
        data_namespace = {}
        exec(data_code, data_namespace)
        
        # Extract data
        xcoord = data_namespace['xcoord']
        ycoord = data_namespace['ycoord']
        N = data_namespace.get('N', len(xcoord))
        
        # Convert to the format expected by the rest of the code
        # Original format: 1-indexed (1, 2, ..., 103)
        # Our code uses: 0-indexed (0, 1, ..., 102) with city names
        coords = {}
        cities = []
        
        for i in range(1, N + 1):
            city_name = f'City{i}'
            coords[city_name] = (float(xcoord[i]), float(ycoord[i]))
            cities.append(city_name)
        
        print(f"Loaded {N} cities from NorwayTSP_Data (1).py")
        return coords, cities
        
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def compute_dist_matrix(coords: Dict[str, Tuple[float, float]], 
                        cities: List[str]) -> Dict[Tuple[int, int], float]:
    """
    Compute Euclidean distance matrix for all city pairs
    
    Args:
        coords: Dictionary mapping city names to (x, y) coordinates
        cities: List of city names (ordered)
    
    Returns:
        Dictionary mapping (i, j) tuples to distance values
    """
    n = len(cities)
    dist_matrix = {}
    
    for i in range(n):
        city_i = cities[i]
        x_i, y_i = coords[city_i]
        for j in range(n):
            if i != j:
                city_j = cities[j]
                x_j, y_j = coords[city_j]
                # Euclidean distance
                dist = math.sqrt((x_i - x_j)**2 + (y_i - y_j)**2)
                dist_matrix[(i, j)] = dist
    
    return dist_matrix


def build_arcs(n: int) -> List[Tuple[int, int]]:
    """
    Build list of all arcs (i, j) where i != j
    
    Args:
        n: Number of cities
    
    Returns:
        List of (i, j) tuples representing arcs
    """
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j))
    return arcs


def setup_logging(model: gp.Model, name: str, log_dir: str = "logs") -> None:
    """
    Setup logging for Gurobi model
    
    Args:
        model: Gurobi model instance
        name: Name identifier for the log file (e.g., "YourName-MTZ")
        log_dir: Directory to save log files
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"TSP-log-{name}.txt")
    model.Params.LogFile = log_file
    model.Params.LogToConsole = 1  # Also print to console


def reconstruct_tour(x: gp.tupledict, n: int) -> List[int]:
    """
    Reconstruct tour from binary decision variables x[i,j]
    
    Args:
        x: Gurobi tupledict of binary variables x[i,j]
        n: Number of cities
    
    Returns:
        List of city indices representing the tour (starting and ending at 0)
    """
    # Build adjacency list
    next_city = {}
    for i in range(n):
        for j in range(n):
            if i != j and x[i, j].X > 0.5:
                next_city[i] = j
    
    # Reconstruct tour starting from city 0
    tour = [0]
    current = 0
    visited = {0}
    
    while len(tour) < n:
        if current in next_city:
            next_c = next_city[current]
            if next_c in visited and len(tour) < n:
                # Subtour detected - break
                break
            tour.append(next_c)
            visited.add(next_c)
            current = next_c
        else:
            break
    
    return tour


def save_solution(model_name: str, name: str, cities: List[str], 
                  tour: List[int], objective: float, runtime: float,
                  num_vars: int, num_constrs: int, 
                  sol_dir: str = "solutions") -> None:
    """
    Save solution to file
    
    Args:
        model_name: Name of the model (MTZ, Svestka, Dantzig)
        name: User name identifier
        cities: List of city names
        tour: List of city indices in tour order
        objective: Objective value
        runtime: Runtime in seconds
        num_vars: Number of variables
        num_constrs: Number of constraints
        sol_dir: Directory to save solution files
    """
    os.makedirs(sol_dir, exist_ok=True)
    
    sol_file = os.path.join(sol_dir, f"TSP-solutions-{model_name}-{name}.txt")
    
    with open(sol_file, 'w', encoding='utf-8') as f:
        f.write(f"TSP Solution - {model_name} Model\n")
        f.write(f"=" * 50 + "\n\n")
        f.write(f"Number of Variables: {num_vars}\n")
        f.write(f"Number of Constraints: {num_constrs}\n")
        f.write(f"Objective Value: {objective:.2f}\n")
        f.write(f"Runtime (seconds): {runtime:.2f}\n\n")
        f.write("Tour:\n")
        f.write("-" * 50 + "\n")
        
        for idx, city_idx in enumerate(tour):
            city_name = cities[city_idx]
            f.write(f"{idx + 1}. {city_name} (City {city_idx})\n")
        
        # Also write the cycle back to start
        if tour and tour[0] == 0:
            f.write(f"{len(tour) + 1}. {cities[0]} (City 0) - Return to start\n")
        
        f.write(f"\nTotal Distance: {objective:.2f}\n")


def get_optimization_params() -> Dict[str, Any]:
    """
    Get optimized Gurobi parameters for TSP solving
    
    Returns:
        Dictionary of parameter name-value pairs
    """
    import os
    
    # For academic licenses, Threads must be >= 0
    # Try to get number of cores, default to 0 (auto) if not available
    try:
        num_threads = os.cpu_count() or 0
        # Academic license may limit threads, so use min(cores, 8) or 0 for auto
        # Setting to 0 lets Gurobi choose (usually uses all available for academic)
        num_threads = min(num_threads, 8) if num_threads > 0 else 0
    except:
        num_threads = 0  # Let Gurobi decide
    
    return {
        'TimeLimit': 3600,
        'Threads': num_threads,  # Use available threads (0 = auto for academic license)
        'MIPFocus': 1,  # Focus on finding feasible solutions quickly
        'Presolve': 2,  # Aggressive presolve
        'Cuts': 2,  # Aggressive cutting
        'Heuristics': 0.25,  # Use 25% of time on heuristics
        'MIPGap': 0.0001,  # Stop when gap is small enough
        'OutputFlag': 1,  # Enable output
    }


# Optional: Plotting function (requires matplotlib)
def plot_tour(tour: List[int], coords: Dict[str, Tuple[float, float]], 
              cities: List[str], title: str = "TSP Tour") -> None:
    """
    Plot the TSP tour (optional visualization)
    
    Args:
        tour: List of city indices in tour order
        coords: Dictionary mapping city names to coordinates
        cities: List of city names
        title: Plot title
    """
    try:
        import matplotlib.pyplot as plt
        
        # Extract coordinates for tour
        x_coords = [coords[cities[i]][0] for i in tour]
        y_coords = [coords[cities[i]][1] for i in tour]
        
        # Close the tour
        x_coords.append(x_coords[0])
        y_coords.append(y_coords[0])
        
        plt.figure(figsize=(10, 8))
        plt.plot(x_coords, y_coords, 'b-o', linewidth=2, markersize=8)
        
        # Annotate cities
        for i, city_idx in enumerate(tour):
            x, y = coords[cities[city_idx]]
            plt.annotate(f"{i+1}. {cities[city_idx]}", (x, y), 
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel('X Coordinate', fontsize=12)
        plt.ylabel('Y Coordinate', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save plot
        os.makedirs('solutions', exist_ok=True)
        plt.savefig(f'solutions/{title.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        print(f"Plot saved to solutions/{title.replace(' ', '_')}.png")
        plt.close()
        
    except ImportError:
        print("matplotlib not available - skipping plot generation")
