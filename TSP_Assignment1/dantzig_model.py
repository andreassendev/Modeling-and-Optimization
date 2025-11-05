"""
Dantzig-Fulkerson-Johnson (DFJ) Formulation for TSP
Using lazy constraints callback for subtour elimination
"""

import sys
import os
import time
from typing import Dict, Tuple, List, Set

# Add utils to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    print("Error: gurobipy not found. Please install it with: pip install gurobipy")
    sys.exit(1)

from utils.base_model import (
    load_data, compute_dist_matrix, build_arcs,
    setup_logging, reconstruct_tour, save_solution, get_optimization_params
)


def find_subtours(x: gp.tupledict, n: int, arcs: List[Tuple[int, int]] = None) -> List[List[int]]:
    """
    Find all subtours in the current solution using DFS
    
    Args:
        x: Gurobi tupledict of binary variables
        n: Number of cities
        arcs: Optional list of arcs (for compatibility)
    
    Returns:
        List of subtours (each subtour is a list of city indices)
    """
    # Build adjacency list from current solution
    adj = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(n):
            if i != j and (i, j) in x and x[i, j].X > 0.5:
                adj[i].append(j)
    
    # DFS to find all connected components
    visited = set()
    subtours = []
    
    for start in range(n):
        if start in visited:
            continue
        
        # DFS from start
        stack = [start]
        component = []
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        
        if len(component) > 1:
            subtours.append(component)
    
    return subtours


def solve_dantzig(name: str = "YourName") -> Dict:
    """
    Solve TSP using Dantzig-Fulkerson-Johnson (DFJ) formulation
    with lazy constraints callback for subtour elimination
    
    DFJ Formulation:
    min sum_{i,j} c_ij * x_ij
    s.t.
        sum_j x_ij = 1 for all i          (outdegree)
        sum_i x_ij = 1 for all j          (indegree)
        sum_{i,j in S} x_ij <= |S| - 1    for all S subset of cities, |S| >= 2 (subtour elimination)
        x_ij in {0,1}
    
    Implementation:
    - Start with degree constraints only
    - Use lazy constraints callback to add subtour elimination constraints on-the-fly
    - Only add constraints for violated subtours
    
    Optimizations:
    1. Lazy constraints reduce problem size initially
    2. Efficient subtour detection using DFS
    3. Optimized Gurobi parameters
    
    Args:
        name: User name identifier for log/solution files
    
    Returns:
        Dictionary with model statistics and results
    """
    print("\n" + "="*60)
    print("Solving TSP with Dantzig-Fulkerson-Johnson (DFJ) Formulation")
    print("Using Lazy Constraints Callback")
    print("="*60)
    
    # Load data
    coords, cities = load_data()
    n = len(cities)
    print(f"Loaded {n} cities")
    
    # Compute distance matrix
    print("Computing distance matrix...")
    dist_matrix = compute_dist_matrix(coords, cities)
    
    # Build arcs (only i ≠ j)
    arcs = build_arcs(n)
    print(f"Number of arcs: {len(arcs)}")
    
    # Create model
    model = gp.Model("TSP_Dantzig")
    model.setParam('OutputFlag', 1)
    
    # Set optimization parameters
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    # CRITICAL: Enable lazy constraints
    model.Params.LazyConstraints = 1
    
    # Setup logging
    setup_logging(model, f"{name}-Dantzig", "logs")
    
    # Decision variables
    # x[i,j] = 1 if arc (i,j) is used, 0 otherwise
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist_matrix[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )
    
    # Outdegree constraints: each city has exactly one outgoing arc
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if (i, j) in arcs) == 1,
            name=f"outdegree_{i}"
        )
    
    # Indegree constraints: each city has exactly one incoming arc
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if (i, j) in arcs) == 1,
            name=f"indegree_{j}"
        )
    
    # Lazy constraints callback
    subtour_count = [0]  # Use list to allow modification in callback
    
    def subtour_elimination_callback(model, where):
        """
        Callback function to add subtour elimination constraints
        Called when a new integer solution is found
        """
        if where == GRB.Callback.MIPSOL:
            # Get callback data from model
            x = model._x
            n = model._n
            arcs = model._arcs
            subtour_count = model._subtour_count
            
            # Get current solution values
            x_vals = model.cbGetSolution(x)
            
            # Build adjacency list directly from solution values
            adj = {i: [] for i in range(n)}
            for (i, j) in arcs:
                if x_vals[i, j] > 0.5:
                    adj[i].append(j)
            
            # DFS to find all connected components (subtours)
            visited = set()
            subtours_found = []
            
            for start in range(n):
                if start in visited:
                    continue
                
                stack = [start]
                component = []
                
                while stack:
                    node = stack.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    component.append(node)
                    
                    for neighbor in adj.get(node, []):
                        if neighbor not in visited:
                            stack.append(neighbor)
                
                if len(component) > 1:
                    subtours_found.append(component)
            
            # Add constraints for each subtour (except if it's the full tour)
            for subtour in subtours_found:
                if len(subtour) < n:
                    # Subtour elimination: sum_{i,j in S} x_ij <= |S| - 1
                    arcs_in_subtour = [
                        (i, j) for i in subtour for j in subtour 
                        if i != j and (i, j) in arcs
                    ]
                    if arcs_in_subtour:
                        model.cbLazy(
                            gp.quicksum(x[i, j] for (i, j) in arcs_in_subtour) 
                            <= len(subtour) - 1
                        )
                        subtour_count[0] += 1
                        if subtour_count[0] % 10 == 1:  # Print occasionally
                            print(f"  Added lazy constraint #{subtour_count[0]} "
                                  f"(subtour size: {len(subtour)})")
    
    # Update model
    model.update()
    
    # Store callback data in model (needed for callback access)
    model._x = x
    model._subtour_count = subtour_count
    model._n = n
    model._arcs = arcs
    
    # Print initial model statistics
    num_vars = model.NumVars
    initial_constrs = model.NumConstrs
    print(f"\nInitial Model Statistics:")
    print(f"  Variables: {num_vars}")
    print(f"  Initial Constraints: {initial_constrs}")
    print(f"  (Subtour elimination constraints will be added lazily)")
    
    # Solve with callback
    print("\nSolving model with lazy constraints callback...")
    start_time = time.time()
    
    # Set callback
    model.optimize(subtour_elimination_callback)
    
    runtime = time.time() - start_time
    
    # Final statistics
    final_constrs = model.NumConstrs
    print(f"\nTotal lazy constraints added: {subtour_count[0]}")
    print(f"Final constraints: {final_constrs}")
    
    # Process results
    if model.status == GRB.OPTIMAL:
        print(f"\n[OK] Optimal solution found!")
        objective = model.ObjVal
        print(f"  Objective value: {objective:.2f}")
        print(f"  Runtime: {runtime:.2f} seconds")
        
        # Reconstruct tour
        tour = reconstruct_tour(x, n)
        print(f"\nTour: {' -> '.join([cities[i] for i in tour])} -> {cities[0]}")
        
        # Save solution
        save_solution("Dantzig", name, cities, tour, objective, runtime,
                     num_vars, final_constrs, "solutions")
        
        return {
            'status': 'Optimal',
            'objective': objective,
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': final_constrs,
            'lazy_constrs': subtour_count[0],
            'tour': tour,
        }
    elif model.status == GRB.TIME_LIMIT:
        print(f"\n[WARNING] Time limit reached")
        if model.SolCount > 0:
            objective = model.ObjVal
            tour = reconstruct_tour(x, n)
            print(f"  Best bound: {model.ObjBound:.2f}")
            print(f"  Gap: {model.MIPGap * 100:.2f}%")
            save_solution("Dantzig", name, cities, tour, objective, runtime,
                         num_vars, final_constrs, "solutions")
            return {
                'status': 'TimeLimit',
                'objective': objective,
                'bound': model.ObjBound,
                'gap': model.MIPGap,
                'runtime': runtime,
                'num_vars': num_vars,
                'num_constrs': final_constrs,
                'lazy_constrs': subtour_count[0],
                'tour': tour,
            }
    else:
        print(f"\n[ERROR] Optimization failed. Status: {model.status}")
        return {
            'status': 'Failed',
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': final_constrs,
        }


if __name__ == "__main__":
    # Run with default name (change as needed)
    result = solve_dantzig("YourName")
    print("\nResult summary:", result)
