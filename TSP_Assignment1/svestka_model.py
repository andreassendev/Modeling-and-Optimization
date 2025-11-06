"""
Svestka Flow-Based Formulation for TSP
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


def solve_svestka(name: str = "MartinAndreassen") -> Dict:
    """
    Løser TSP med Svestka flow-basert formulering
    """
    coords, cities = load_data()
    n = len(cities)
    
    dist_matrix = compute_dist_matrix(coords, cities)
    arcs = build_arcs(n)
    
    model = gp.Model("TSP_Svestka")
    model.setParam('OutputFlag', 1)
    
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    setup_logging(model, f"{name}-Svestka", "logs")
    
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    f = model.addVars(arcs, lb=0, ub=n-1, vtype=GRB.CONTINUOUS, name="f")
    
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
    
    model.addConstr(
        gp.quicksum(f[0, j] for j in range(1, n) if (0, j) in arcs) == n - 1,
        name="flow_source"
    )
    
    model.addConstr(
        gp.quicksum(f[i, 0] for i in range(1, n) if (i, 0) in arcs) == 0,
        name="flow_sink"
    )
    
    for i in range(1, n):
        outgoing = gp.quicksum(f[i, j] for j in range(n) if (i, j) in arcs)
        incoming = gp.quicksum(f[j, i] for j in range(n) if (j, i) in arcs)
        model.addConstr(
            outgoing - incoming == -1,
            name=f"flow_balance_{i}"
        )
    
    for (i, j) in arcs:
        if i == 0 or j == 0:
            model.addConstr(
                f[i, j] <= (n - 1) * x[i, j],
                name=f"link_0_{i}_{j}"
            )
        else:
            model.addConstr(
                f[i, j] <= (n - 2) * x[i, j],
                name=f"link_{i}_{j}"
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
        
        print(f"\nSvestka")
        print(f"Antall variabler: {num_vars}")
        print(f"Antall begrensninger: {num_constrs}")
        print(f"Målverdi: {objective:.2f}")
        print(f"Kjøretid: {runtime:.2f} sekunder")
        
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
        if model.SolCount > 0:
            objective = model.ObjVal
            tour = reconstruct_tour(x, n)
            
            print(f"\nSvestka")
            print(f"Antall variabler: {num_vars}")
            print(f"Antall begrensninger: {num_constrs}")
            print(f"Målverdi: {objective:.2f}")
            print(f"Kjøretid: {runtime:.2f} sekunder")
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
        print(f"\nSvestka")
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
    solve_svestka("MartinAndreassen")
