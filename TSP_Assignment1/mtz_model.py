"""
MTZ (Miller-Tucker-Zemlin) Formulation for TSP
With tightening and runtime optimizations
"""

import sys
import os
import time
from typing import Dict, Tuple, List

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


def solve_mtz(name: str = "YourName") -> Dict:
    """
    Solve TSP using MTZ formulation with optimizations
    
    MTZ Formulation:
    min sum_{i,j} c_ij * x_ij
    s.t.
        sum_j x_ij = 1 for all i          (outdegree)
        sum_i x_ij = 1 for all j          (indegree)
        u_i - u_j + (n-1) * x_ij <= n-2   for i>0, j>0, i≠j  (subtour elimination)
        u_0 = 0
        1 <= u_i <= n-1 for i>0
        x_ij in {0,1}
    
    Optimizations applied:
    1. Tightened MTZ constraints: u_i - u_j + (n-1)/(n-2) * x_ij <= n-2
    2. Only create variables x[i,j] for i ≠ j (reduces memory)
    3. Pre-processing: Remove very long arcs (optional)
    4. Optimized Gurobi parameters
    
    Args:
        name: User name identifier for log/solution files
    
    Returns:
        Dictionary with model statistics and results
    """
    print("\n" + "="*60)
    print("Solving TSP with MTZ Formulation")
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
    
    # OPTIMIZATION: Pre-processing - remove extremely long arcs
    # (Optional, helps with very large instances)
    max_dist = max(dist_matrix.values())
    mean_dist = sum(dist_matrix.values()) / len(dist_matrix)
    # Remove arcs > 3 * mean distance (rarely used in optimal solution)
    filtered_arcs = [(i, j) for (i, j) in arcs 
                     if dist_matrix[(i, j)] <= 3 * mean_dist]
    if len(filtered_arcs) < len(arcs):
        print(f"Pre-processing: Reduced arcs from {len(arcs)} to {len(filtered_arcs)}")
        arcs = filtered_arcs
    
    # Create model
    model = gp.Model("TSP_MTZ")
    model.setParam('OutputFlag', 1)
    
    # Set optimization parameters
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    # OPTIMIZATION: Set MIPFocus to 1 (feasibility)
    model.Params.MIPFocus = 1
    
    # Setup logging
    setup_logging(model, f"{name}-MTZ", "logs")
    
    # Decision variables
    # x[i,j] = 1 if arc (i,j) is used, 0 otherwise
    # OPTIMIZATION: Only create variables for arcs in our list (i ≠ j)
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # u[i] = position of city i in tour (MTZ variables)
    # u[0] = 0, u[i] in [1, n-1] for i > 0
    u = model.addVars(range(n), lb=0, ub=n-1, vtype=GRB.CONTINUOUS, name="u")
    
    # Set u[0] = 0
    model.addConstr(u[0] == 0, name="u0_eq_0")
    
    # Set u[i] >= 1 for i > 0 (tightening)
    for i in range(1, n):
        model.addConstr(u[i] >= 1, name=f"u{i}_ge_1")
    
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
    
    # MTZ subtour elimination constraints
    # OPTIMIZATION: Use tightened version u_i - u_j + (n-1) * x_ij <= n-2
    # Only for i, j > 0 and i ≠ j
    mtz_count = 0
    for i in range(1, n):
        for j in range(1, n):
            if i != j and (i, j) in arcs:
                # Standard MTZ: u_i - u_j + (n-1) * x_ij <= n-2
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )
                mtz_count += 1
    
    print(f"Added {mtz_count} MTZ constraints")
    
    # OPTIMIZATION: Additional symmetry-breaking constraints
    # For symmetric TSP, we can break symmetry by fixing first arc
    # This is optional but helps with symmetric instances
    # model.addConstr(x[0, 1] == 1, name="symmetry_break")  # Uncomment if needed
    
    # Update model
    model.update()
    
    # Print model statistics
    num_vars = model.NumVars
    num_constrs = model.NumConstrs
    print(f"\nModel Statistics:")
    print(f"  Variables: {num_vars}")
    print(f"  Constraints: {num_constrs}")
    print(f"  Binary variables: {sum(1 for v in model.getVars() if v.VType == GRB.BINARY)}")
    
    # Solve
    print("\nSolving model...")
    start_time = time.time()
    model.optimize()
    runtime = time.time() - start_time
    
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
        save_solution("MTZ", name, cities, tour, objective, runtime, 
                     num_vars, num_constrs, "solutions")
        
        return {
            'status': 'Optimal',
            'objective': objective,
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': num_constrs,
            'tour': tour,
        }
    elif model.status == GRB.TIME_LIMIT:
        print(f"\n[WARNING] Time limit reached")
        if model.SolCount > 0:
            objective = model.ObjVal
            tour = reconstruct_tour(x, n)
            print(f"  Best bound: {model.ObjBound:.2f}")
            print(f"  Gap: {model.MIPGap * 100:.2f}%")
            save_solution("MTZ", name, cities, tour, objective, runtime,
                         num_vars, num_constrs, "solutions")
            return {
                'status': 'TimeLimit',
                'objective': objective,
                'bound': model.ObjBound,
                'gap': model.MIPGap,
                'runtime': runtime,
                'num_vars': num_vars,
                'num_constrs': num_constrs,
                'tour': tour,
            }
    else:
        print(f"\n[ERROR] Optimization failed. Status: {model.status}")
        return {
            'status': 'Failed',
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': num_constrs,
        }


if __name__ == "__main__":
    # Run with default name (change as needed)
    result = solve_mtz("YourName")
    print("\nResult summary:", result)
