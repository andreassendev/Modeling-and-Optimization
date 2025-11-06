"""
MTZ (Miller-Tucker-Zemlin) Formulering for TSP
"""

import sys
import os
import time
from typing import Dict, Tuple, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    print("Feil: gurobipy ikke funnet. Installer med: pip install gurobipy")
    sys.exit(1)

from utils.base_model import (
    load_data, compute_dist_matrix, build_arcs, 
    setup_logging, reconstruct_tour, save_solution, get_optimization_params
)


def solve_mtz(name: str = "MartinAndreassen") -> Dict:
    """
    Løser TSP med MTZ formulering
    """
    coords, cities = load_data()
    n = len(cities)
    
    dist_matrix = compute_dist_matrix(coords, cities)
    arcs = build_arcs(n)
    
    mean_dist = sum(dist_matrix.values()) / len(dist_matrix)
    filtered_arcs = [(i, j) for (i, j) in arcs 
                     if dist_matrix[(i, j)] <= 3 * mean_dist]
    if len(filtered_arcs) < len(arcs):
        arcs = filtered_arcs
    
    model = gp.Model("TSP_MTZ")
    model.setParam('OutputFlag', 1)
    
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    model.Params.MIPFocus = 1
    
    setup_logging(model, f"{name}-MTZ", "logs")
    
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    u = model.addVars(range(n), lb=0, ub=n-1, vtype=GRB.CONTINUOUS, name="u")
    
    model.addConstr(u[0] == 0, name="u0_eq_0")
    
    for i in range(1, n):
        model.addConstr(u[i] >= 1, name=f"u{i}_ge_1")
    
    model.setObjective(
        gp.quicksum(dist_matrix[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )
    
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if (i, j) in arcs) == 1,
            name=f"outdegree_{i}"
        )
    
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if (i, j) in arcs) == 1,
            name=f"indegree_{j}"
        )
    
    for i in range(1, n):
        for j in range(1, n):
            if i != j and (i, j) in arcs:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )
    
    model.update()
    
    num_vars = model.NumVars
    num_constrs = model.NumConstrs
    
    start_time = time.time()
    model.optimize()
    runtime = time.time() - start_time
    
    if model.status == GRB.OPTIMAL:
        objective = model.ObjVal
        tour = reconstruct_tour(x, n)
        
        print(f"\nMTZ")
        print(f"Antall variabler: {num_vars}")
        print(f"Antall begrensninger: {num_constrs}")
        print(f"Målverdi: {objective:.2f}")
        print(f"Kjøretid: {runtime:.2f} sekunder")
        
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
        if model.SolCount > 0:
            objective = model.ObjVal
            tour = reconstruct_tour(x, n)
            
            print(f"\nMTZ")
            print(f"Antall variabler: {num_vars}")
            print(f"Antall begrensninger: {num_constrs}")
            print(f"Målverdi: {objective:.2f}")
            print(f"Kjøretid: {runtime:.2f} sekunder")
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
        print(f"\nMTZ")
        print(f"Antall variabler: {num_vars}")
        print(f"Antall begrensninger: {num_constrs}")
        print(f"Status: Feilet")
        return {
            'status': 'Failed',
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': num_constrs,
        }


if __name__ == "__main__":
    solve_mtz("MartinAndreassen")
