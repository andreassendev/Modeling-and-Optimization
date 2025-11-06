"""
Basis hjelpefunksjoner for TSP modeller
"""

import sys
import os
import math
from typing import Dict, Tuple, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    print("Feil: gurobipy ikke funnet. Installer med: pip install gurobipy")
    sys.exit(1)


def load_data() -> Tuple[Dict[str, Tuple[float, float]], List[str]]:
    """
    Laster koordinatdata fra NorwayTSP_Data
    """
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_file = os.path.join(current_dir, "NorwayTSP_Data (1).py")
        
        if not os.path.exists(data_file):
            data_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'NorwayTSP_Data.py')
            if os.path.exists(data_file):
                sys.path.append(os.path.dirname(data_file))
                from NorwayTSP_Data import NORWAY_COORDINATES
                cities = list(NORWAY_COORDINATES.keys())
                coords = NORWAY_COORDINATES
                return coords, cities
            else:
                raise FileNotFoundError(f"Fant ikke NorwayTSP_Data (1).py i {current_dir}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data_code = f.read()
        
        data_namespace = {}
        exec(data_code, data_namespace)
        
        xcoord = data_namespace['xcoord']
        ycoord = data_namespace['ycoord']
        N = data_namespace.get('N', len(xcoord))
        
        coords = {}
        cities = []
        
        for i in range(1, N + 1):
            city_name = f'City{i}'
            coords[city_name] = (float(xcoord[i]), float(ycoord[i]))
            cities.append(city_name)
        
        return coords, cities
        
    except Exception as e:
        print(f"Feil ved lasting av data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def compute_dist_matrix(coords: Dict[str, Tuple[float, float]], 
                        cities: List[str]) -> Dict[Tuple[int, int], float]:
    """
    Beregner euklidisk distansematrise for alle bypar
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
                dist = math.sqrt((x_i - x_j)**2 + (y_i - y_j)**2)
                dist_matrix[(i, j)] = dist
    
    return dist_matrix


def build_arcs(n: int) -> List[Tuple[int, int]]:
    """
    Bygger liste over alle buer (i, j) hvor i != j
    """
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j))
    return arcs


def setup_logging(model: gp.Model, name: str, log_dir: str = "logs") -> None:
    """
    Setter opp logging for Gurobi modell
    """
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"TSP-log-{name}.txt")
    model.Params.LogFile = log_file
    model.Params.LogToConsole = 1


def reconstruct_tour(x: gp.tupledict, n: int) -> List[int]:
    """
    Rekonstruerer tur fra binære beslutningsvariabler x[i,j]
    """
    next_city = {}
    for i in range(n):
        for j in range(n):
            if i != j and x[i, j].X > 0.5:
                next_city[i] = j
    
    tour = [0]
    current = 0
    visited = {0}
    
    while len(tour) < n:
        if current in next_city:
            next_c = next_city[current]
            if next_c in visited and len(tour) < n:
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
    Lagrer løsning til fil
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
    Henter optimerte Gurobi parametere for TSP løsning
    """
    import os
    
    try:
        num_threads = os.cpu_count() or 0
        num_threads = min(num_threads, 8) if num_threads > 0 else 0
    except:
        num_threads = 0
    
    return {
        'TimeLimit': 3600,
        'Threads': num_threads,
        'MIPFocus': 1,
        'Presolve': 2,
        'Cuts': 2,
        'Heuristics': 0.25,
        'MIPGap': 0.0001,
        'OutputFlag': 1,
    }


def plot_tour(tour: List[int], coords: Dict[str, Tuple[float, float]], 
              cities: List[str], title: str = "TSP Tour") -> None:
    """
    Plotter TSP tur (valgfri visualisering)
    """
    try:
        import matplotlib.pyplot as plt
        
        x_coords = [coords[cities[i]][0] for i in tour]
        y_coords = [coords[cities[i]][1] for i in tour]
        
        x_coords.append(x_coords[0])
        y_coords.append(y_coords[0])
        
        plt.figure(figsize=(10, 8))
        plt.plot(x_coords, y_coords, 'b-o', linewidth=2, markersize=8)
        
        for i, city_idx in enumerate(tour):
            x, y = coords[cities[city_idx]]
            plt.annotate(f"{i+1}. {cities[city_idx]}", (x, y), 
                        xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel('X Coordinate', fontsize=12)
        plt.ylabel('Y Coordinate', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        os.makedirs('solutions', exist_ok=True)
        plt.savefig(f'solutions/{title.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
        print(f"Plot lagret til solutions/{title.replace(' ', '_')}.png")
        plt.close()
        
    except ImportError:
        print("matplotlib ikke tilgjengelig - hopper over plot generering")
