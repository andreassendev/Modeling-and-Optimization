"""
Dantzig-Fulkerson-Johnson (DFJ) Formulering for TSP
Bruker lazy constraints callback for subtour eliminering
"""

import sys
import os
import time
from typing import Dict, Tuple, List, Set

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


def find_subtours(x: gp.tupledict, n: int, arcs: List[Tuple[int, int]] = None) -> List[List[int]]:
    """
    Finner alle subtours i løsningen ved hjelp av DFS
    """
    adj = {i: [] for i in range(n)}
    for i in range(n):
        for j in range(n):
            if i != j and (i, j) in x and x[i, j].X > 0.5:
                adj[i].append(j)
    
    visited = set()
    subtours = []
    
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
            subtours.append(component)
    
    return subtours


def solve_dantzig(name: str = "MartinAndreassen") -> Dict:
    """
    Løser TSP med Dantzig-Fulkerson-Johnson (DFJ) formulering
    Bruker lazy constraints callback for subtour eliminering
    """
    coords, cities = load_data()
    n = len(cities)
    
    dist_matrix = compute_dist_matrix(coords, cities)
    arcs = build_arcs(n)
    
    model = gp.Model("TSP_Dantzig")
    model.setParam('OutputFlag', 1)
    
    params = get_optimization_params()
    for param_name, param_value in params.items():
        model.setParam(param_name, param_value)
    
    model.Params.LazyConstraints = 1
    
    setup_logging(model, f"{name}-Dantzig", "logs")
    
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")
    
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
    
    subtour_count = [0]
    
    def subtour_elimination_callback(model, where):
        """
        Callback funksjon som legger til subtour eliminering begrensninger
        """
        if where == GRB.Callback.MIPSOL:
            x = model._x
            n = model._n
            arcs = model._arcs
            subtour_count = model._subtour_count
            
            x_vals = model.cbGetSolution(x)
            
            adj = {i: [] for i in range(n)}
            for (i, j) in arcs:
                if x_vals[i, j] > 0.5:
                    adj[i].append(j)
            
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
            
            for subtour in subtours_found:
                if len(subtour) < n:
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
    
    model.update()
    
    model._x = x
    model._subtour_count = subtour_count
    model._n = n
    model._arcs = arcs
    
    num_vars = model.NumVars
    
    start_time = time.time()
    model.optimize(subtour_elimination_callback)
    runtime = time.time() - start_time
    
    final_constrs = model.NumConstrs
    
    if model.status == GRB.OPTIMAL:
        objective = model.ObjVal
        tour = reconstruct_tour(x, n)
        
        print(f"\nDantzig")
        print(f"Antall variabler: {num_vars}")
        print(f"Antall begrensninger: {final_constrs}")
        print(f"Målverdi: {objective:.2f}")
        print(f"Kjøretid: {runtime:.2f} sekunder")
        
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
        if model.SolCount > 0:
            objective = model.ObjVal
            tour = reconstruct_tour(x, n)
            
            print(f"\nDantzig")
            print(f"Antall variabler: {num_vars}")
            print(f"Antall begrensninger: {final_constrs}")
            print(f"Målverdi: {objective:.2f}")
            print(f"Kjøretid: {runtime:.2f} sekunder")
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
        print(f"\nDantzig")
        print(f"Antall variabler: {num_vars}")
        print(f"Antall begrensninger: {final_constrs}")
        print(f"Status: Feilet")
        return {
            'status': 'Failed',
            'runtime': runtime,
            'num_vars': num_vars,
            'num_constrs': final_constrs,
        }


if __name__ == "__main__":
    solve_dantzig("MartinAndreassen")
