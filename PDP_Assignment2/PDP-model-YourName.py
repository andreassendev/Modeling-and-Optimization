"""
INF170 Assignment 2 – Q2: Pickup & Delivery Problem
Formulering EXACT (1)–(16) som gitt av studenten.

Ingen omskriving av ulikheter – vi implementerer samme retning og ledd.
"""

import os
import sys
from gurobipy import Model, GRB, quicksum

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import data
# Since file name contains hyphens, we use importlib to load it
import importlib.util

data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PDP-data-YourName.py")
spec = importlib.util.spec_from_file_location("pdp_data", data_file)
pdp_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdp_data)

Nv = pdp_data.Nv
Np = pdp_data.Np
Nd = pdp_data.Nd
A = pdp_data.A
D = pdp_data.D
Q = pdp_data.Q
K = pdp_data.K
CS = pdp_data.CS
o = pdp_data.o
d = pdp_data.d
n = pdp_data.n
BigM = pdp_data.BigM


# Create model
m = Model("PDP")

# Variabler
x = m.addVars(A, vtype=GRB.BINARY, name="x")                         # x_ij ∈ {0,1}
y = m.addVars(Np, vtype=GRB.BINARY, name="y")                        # y_i ∈ {0,1}
t = m.addVars(Nv, lb=0.0, vtype=GRB.CONTINUOUS, name="t")            # t_i ≥ 0
l = m.addVars(Nv, lb=0.0, ub=K, vtype=GRB.CONTINUOUS, name="l")      # 0 ≤ l_i ≤ K

# (1) Objective:
# M in Z = sum_{(i,j)∈A:i≠j} D_ij x_ij + sum_{i∈Np} C_S y_i
m.setObjective(
    quicksum(D[i][j] * x[i, j] for (i, j) in A if i != j)
    + quicksum(CS * y[i] for i in Np),
    GRB.MINIMIZE
)

# (2) sum_{(i,j)∈A:i≠j} x_ij + y_i = 1,  i ∈ Np
for i in Np:
    m.addConstr(
        quicksum(x[i, j] for j in Nv if (i, j) in A and i != j) + y[i] == 1,
        name=f"eq2_alloc[{i}]"
    )

# (3) sum_{j∈Nv:j≠o} x_oj = 1
m.addConstr(
    quicksum(x[o, j] for j in Nv if j != o and (o, j) in A) == 1,
    name="eq3_leave_origin"
)

# (4) sum_{(i,j)∈A:i≠j} x_ij − sum_{(w,i)∈A:i≠w} x_wi = 0,  i ∈ Nv\{o,d}
for i in Nv:
    if i != o and i != d:
        m.addConstr(
            quicksum(x[i, j] for j in Nv if (i, j) in A and i != j)
            - quicksum(x[w, i] for w in Nv if (w, i) in A and i != w)
            == 0,
            name=f"eq4_flow[{i}]"
        )

# (5) sum_{j∈Nv:j≠d} x_jd = 1   (merk: oppgaveteksten bruker x_jd; vi skriver som inn-til d)
m.addConstr(
    quicksum(x[i, d] for i in Nv if i != d and (i, d) in A) == 1,
    name="eq5_enter_dest"
)

# (6) l_i + Q_j − l_j ≤ K(1 − x_ij),  j ∈ Np, (i,j)∈A:i≠j
for (i, j) in A:
    if j in Np and i != j:
        m.addConstr(
            l[i] + Q[j] - l[j] <= K * (1 - x[i, j]),
            name=f"eq6_load_pick[{i},{j}]"
        )

# (7) l_i − Q_j − l_{n+j} ≤ K(1 − x_{i, n+j}),  j ∈ Np, (i,n+j)∈A:i≠n+j
for j in Np:
    del_node = n + j
    for i in Nv:
        if i != del_node and (i, del_node) in A:
            m.addConstr(
                l[i] - Q[j] - l[del_node] <= K * (1 - x[i, del_node]),
                name=f"eq7_load_del[{i},{del_node}]"
            )

# (8) 0 ≤ l_i ≤ K,  i ∈ Nv
# (reflektert i variabeldefinisjonene; vi legger dem eksplisitt også for sporbarhet)
for i in Nv:
    m.addConstr(l[i] >= 0.0, name=f"eq8_lb[{i}]")
    m.addConstr(l[i] <= K, name=f"eq8_ub[{i}]")

# (9) t_0 + D_ij − t_j ≤ M * (1 − x_ij),  (i,j)∈A:i≠j, i = o
for j in Nv:
    if j != o and (o, j) in A:
        m.addConstr(
            0.0 + D[o][j] - t[j] <= BigM * (1 - x[o, j]),
            name=f"eq9_time_from_origin[{o},{j}]"
        )

# (10) t_i + D_ij − t_j ≤ M * (1 − x_ij),  (i,j)∈A:i≠j, i ≠ o
for (i, j) in A:
    if i != j and i != o:
        m.addConstr(
            t[i] + D[i][j] - t[j] <= BigM * (1 - x[i, j]),
            name=f"eq10_time_arc[{i},{j}]"
        )

# (11) sum_{(i,j)∈A:i≠j} x_ij − sum_{(n+i,j)∈A:n+i≠j} x_{(n+i)j} = 0,  i ∈ Np
for i in Np:
    del_node = n + i
    lhs1 = quicksum(x[i, j] for j in Nv if (i, j) in A and i != j)
    lhs2 = quicksum(x[del_node, j] for j in Nv if (del_node, j) in A and del_node != j)
    m.addConstr(lhs1 - lhs2 == 0, name=f"eq11_pick_del_balance[{i}]")

# (12) t_i + D_{i, n+i} − t_{n+i} ≤ 0,  i ∈ Np
for i in Np:
    del_node = n + i
    if (i, del_node) in A:
        m.addConstr(
            t[i] + D[i][del_node] - t[del_node] <= 0.0,
            name=f"eq12_pick_before_delivery[{i}]"
        )
    else:
        # hvis direktebuen ikke finnes, håndhev svak rekkefølge (t_{n+i} ≥ t_i)
        m.addConstr(
            t[del_node] - t[i] >= 0.0,
            name=f"eq12_pick_before_delivery_weak[{i}]"
        )

# (13) y_i ∈ {0, 1}, i ∈ Np        -> vtype=GRB.BINARY i definisjon
# (14) x_ij ∈ {0, 1}, i≠j          -> vtype=GRB.BINARY i definisjon (A ekskluderer i=j)
# (15) l_i ≥ 0, i ∈ Nv             -> lb=0 i definisjon (+ eq8)
# (16) t_i ≥ 0, i ∈ Nv             -> lb=0 i definisjon

# Gurobi-parametere (hastighet/robusthet)
os.makedirs("logs", exist_ok=True)
m.Params.TimeLimit = 3600
m.Params.MIPFocus = 1
m.Params.Presolve = 2
m.Params.Cuts = 2
m.Params.Heuristics = 0.25
m.Params.MIPGap = 1e-4
m.Params.Threads = 0  # 0 = auto (academic license doesn't support -1)
m.Params.LogFile = "logs/PDP-log-YourName.txt"
m.Params.OutputFlag = 1

print("=" * 60)
print("PDP Model - Constraints (1)-(16)")
print("=" * 60)
print(f"Number of nodes: {len(Nv)}")
print(f"Number of pickups: {len(Np)}")
print(f"Number of arcs: {len(A)}")
print(f"BigM: {BigM:.2f}")
print(f"Vehicle capacity: {K}")
print(f"Spot charter cost: {CS}")
print("=" * 60)

m.optimize()

# Output
os.makedirs(".", exist_ok=True)
with open("PDP-solution-YourName.txt", "w", encoding="utf-8") as f:
    f.write("PDP Solution\n")
    f.write("=" * 60 + "\n")
    f.write(f"Status: {m.Status}\n")
    
    if m.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        if m.Status == GRB.OPTIMAL:
            f.write("[OK] Optimal solution found!\n")
        elif m.Status == GRB.TIME_LIMIT:
            f.write("[INFO] Time limit reached, best found solution reported.\n")
        else:
            f.write("[INFO] Best feasible solution reported.\n")
        
        f.write(f"Objective: {m.ObjVal:.6f}\n")
        f.write(f"Runtime: {m.Runtime:.2f} s\n")
        f.write(f"Num Vars: {m.NumVars}\n")
        f.write(f"Num Constrs: {m.NumConstrs}\n\n")
        
        f.write("Selected arcs (x[i,j]=1):\n")
        f.write("-" * 60 + "\n")
        arcs_used = []
        for (i, j) in A:
            if x[i, j].X > 0.5:
                arcs_used.append((i, j))
                f.write(f"  {i} -> {j}  (distance: {D[i][j]:.2f})\n")
        
        f.write("\nSpot charter decisions (y[i]=1 means pickup i uses spot charter):\n")
        f.write("-" * 60 + "\n")
        for i in Np:
            if y[i].X > 0.5:
                f.write(f"  Pickup {i}: Uses spot charter (cost: {CS:.2f})\n")
            else:
                f.write(f"  Pickup {i}: Served by vehicle\n")
        
        f.write("\nTime variables (t[i]):\n")
        f.write("-" * 60 + "\n")
        for i in Nv:
            if i in [o, d]:
                f.write(f"  Node {i} ({'origin' if i == o else 'destination'}): t = {t[i].X:.2f}\n")
            elif i in Np:
                f.write(f"  Node {i} (pickup): t = {t[i].X:.2f}\n")
            elif i in Nd:
                f.write(f"  Node {i} (delivery): t = {t[i].X:.2f}\n")
        
        f.write("\nLoad variables (l[i]):\n")
        f.write("-" * 60 + "\n")
        for i in Nv:
            if i in [o, d]:
                f.write(f"  Node {i} ({'origin' if i == o else 'destination'}): l = {l[i].X:.2f}\n")
            elif i in Np:
                f.write(f"  Node {i} (pickup): l = {l[i].X:.2f} (load +{Q[i]:.2f})\n")
            elif i in Nd:
                pickup_for_del = i - n
                f.write(f"  Node {i} (delivery of pickup {pickup_for_del}): l = {l[i].X:.2f} (load -{Q[pickup_for_del]:.2f})\n")
    else:
        f.write(f"[ERROR] Optimization failed with status: {m.Status}\n")
        if m.Status == GRB.INFEASIBLE:
            f.write("Model is infeasible. Check constraints and data.\n")
        elif m.Status == GRB.UNBOUNDED:
            f.write("Model is unbounded. Check objective function.\n")

print("\nDone. See PDP-solution-YourName.txt and logs/PDP-log-YourName.txt")

