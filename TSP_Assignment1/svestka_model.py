"""
Svestka Flow-Based Formulation for TSP
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


def solve_svestka(name: str = "YourName") -> Dict:
    """
    Solve TSP using Svestka flow-based formulation
    
    Svestka Formulation:
    min sum_{i,j} c_ij * x_ij
    s.t.
        sum_j x_ij = 1 for all i          (outdegree)
        sum_i x_ij = 1 for all j          (indegree)
        
        Flow balance:
            sum_j f_0j = n-1              (source: city 0 sends n-1 units)
            sum_i f_i0 = 0                (sink: city 0 receives 0)
            sum_j f_ij - sum_k f_ki = -1  for i > 0 (other cities: net -1)
        
        Linking constraints:
            f_ij <= (n-1) * x_ij          for all (i,j), i=0 or j=0
            f_ij <= (n-2) * x_ij          for all (i,j), i>0, j>0
        
        f_ij >= 0
    
    Optimizations:
    1. Tightened linking constraints
    2. Only create flow variables for arcs in model (reduces memory)
    3. Optimized Gurobi parameters
    
    Args:
        name: User name identifier for log/solution files
    
    Returns:
        Dictionary with model statistics and results
    """
    print("\n" + "="*60)
    print("Solving TSP with Svestka Flow-Based Formulation")
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
    model = gp.Model("TSP_Svestka")
    model.setParam('OutputFlag', 1)
    
    # Set optimization parameters
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    # Setup logging
    setup_logging(model, f"{name}-Svestka", "logs")
    
    # Decision variables
    # x[i,j] = 1 if arc (i,j) is used, 0 otherwise
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
    # f[i,j] = flow on arc (i,j)
    # OPTIMIZATION: Only create flow variables for arcs we need
    # For arcs from/to city 0: f_ij <= (n-1) * x_ij
    # For other arcs: f_ij <= (n-2) * x_ij
    f = model.addVars(arcs, lb=0, ub=n-1, vtype=GRB.CONTINUOUS, name="f")
    
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
    
    # Flow balance constraints
    # City 0 (source): sends n-1 units
    model.addConstr(
        gp.quicksum(f[0, j] for j in range(1, n) if (0, j) in arcs) == n - 1,
        name="flow_source"
    )
    
    # City 0 (sink): receives 0 units
    model.addConstr(
        gp.quicksum(f[i, 0] for i in range(1, n) if (i, 0) in arcs) == 0,
        name="flow_sink"
    )
    
    # Other cities: net flow = -1 (receive one unit)
    for i in range(1, n):
        outgoing = gp.quicksum(f[i, j] for j in range(n) if (i, j) in arcs)
        incoming = gp.quicksum(f[j, i] for j in range(n) if (j, i) in arcs)
        model.addConstr(
            outgoing - incoming == -1,
            name=f"flow_balance_{i}"
        )
    
    # Linking constraints (tightening)
    # For arcs involving city 0: f_ij <= (n-1) * x_ij
    for (i, j) in arcs:
        if i == 0 or j == 0:
            model.addConstr(
                f[i, j] <= (n - 1) * x[i, j],
                name=f"link_0_{i}_{j}"
            )
        else:
            # For other arcs: f_ij <= (n-2) * x_ij (tighter bound)
            model.addConstr(
                f[i, j] <= (n - 2) * x[i, j],
                name=f"link_{i}_{j}"
            )
    
    # Update model
    model.update()
    
    # Print model statistics
    num_vars = model.NumVars
    num_constrs = model.NumConstrs
    print(f"\nModel Statistics:")
    print(f"  Variables: {num_vars}")
    print(f"  Constraints: {num_constrs}")
    print(f"  Binary variables: {sum(1 for v in model.getVars() if v.VType == GRB.BINARY)}")
    print(f"  Continuous variables: {sum(1 for v in model.getVars() if v.VType == GRB.CONTINUOUS)}")
    
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
        save_solution("Svestka", name, cities, tour, objective, runtime,
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
            save_solution("Svestka", name, cities, tour, objective, runtime,
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
    result = solve_svestka("YourName")
    print("\nResult summary:", result)
