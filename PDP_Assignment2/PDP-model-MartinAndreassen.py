"""
INF170 Assignment 2 – Q2: Pickup & Delivery Problem
"""

import os
import sys
from gurobipy import Model, GRB, quicksum
import importlib.util

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PDP-data-MartinAndreassen.py")
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


m = Model("PDP")

# Variabler
x = m.addVars(A, vtype=GRB.BINARY, name="x")
y = m.addVars(Np, vtype=GRB.BINARY, name="y")
t = m.addVars(Nv, lb=0.0, vtype=GRB.CONTINUOUS, name="t")
l = m.addVars(Nv, lb=0.0, ub=K, vtype=GRB.CONTINUOUS, name="l")

# (1) Målfunksjon: Minimere total distanse + spot charter kostnad
m.setObjective(
    quicksum(D[i][j] * x[i, j] for (i, j) in A if i != j)
    + quicksum(CS * y[i] for i in Np),
    GRB.MINIMIZE
)

# (2) Allokering: Hver pickup må enten bli betjent av kjøretøy eller spot charter
for i in Np:
    m.addConstr(
        quicksum(x[i, j] for j in Nv if (i, j) in A and i != j) + y[i] == 1,
        name=f"eq2_alloc[{i}]"
    )

# (3) Kjøretøyet må forlate origin
m.addConstr(
    quicksum(x[o, j] for j in Nv if j != o and (o, j) in A) == 1,
    name="eq3_leave_origin"
)

# (4) Flytbalanse: For alle noder unntatt origin og destinasjon må innflyt = utflyt
for i in Nv:
    if i != o and i != d:
        m.addConstr(
            quicksum(x[i, j] for j in Nv if (i, j) in A and i != j)
            - quicksum(x[w, i] for w in Nv if (w, i) in A and i != w)
            == 0,
            name=f"eq4_flow[{i}]"
        )

# (5) Kjøretøyet må ankomme destinasjon
m.addConstr(
    quicksum(x[i, d] for i in Nv if i != d and (i, d) in A) == 1,
    name="eq5_enter_dest"
)

# (6) Lastbegrensning ved pickup: Last etter pickup må respektere kapasitet
for (i, j) in A:
    if j in Np and i != j:
        m.addConstr(
            l[i] + Q[j] - l[j] <= K * (1 - x[i, j]),
            name=f"eq6_load_pick[{i},{j}]"
        )

# (7) Lastbegrensning ved levering: Last etter levering må respektere kapasitet
for j in Np:
    del_node = n + j
    for i in Nv:
        if i != del_node and (i, del_node) in A:
            m.addConstr(
                l[i] - Q[j] - l[del_node] <= K * (1 - x[i, del_node]),
                name=f"eq7_load_del[{i},{del_node}]"
            )

# (8) Lastgrenser: Last må være mellom 0 og kapasitet K
for i in Nv:
    m.addConstr(l[i] >= 0.0, name=f"eq8_lb[{i}]")
    m.addConstr(l[i] <= K, name=f"eq8_ub[{i}]")

# (9) Tidsbegrensning fra origin: Tiden ved neste node må være minst reisetid fra origin
for j in Nv:
    if j != o and (o, j) in A:
        m.addConstr(
            0.0 + D[o][j] - t[j] <= BigM * (1 - x[o, j]),
            name=f"eq9_time_from_origin[{o},{j}]"
        )

# (10) Tidsbegrensning: Tiden ved neste node må være minst nåværende tid + reisetid
for (i, j) in A:
    if i != j and i != o:
        m.addConstr(
            t[i] + D[i][j] - t[j] <= BigM * (1 - x[i, j]),
            name=f"eq10_time_arc[{i},{j}]"
        )

# (11) Pickup-leveringsbalanse: Hvis pickup besøkes, må tilhørende levering også besøkes
for i in Np:
    del_node = n + i
    lhs1 = quicksum(x[i, j] for j in Nv if (i, j) in A and i != j)
    lhs2 = quicksum(x[del_node, j] for j in Nv if (del_node, j) in A and del_node != j)
    m.addConstr(lhs1 - lhs2 == 0, name=f"eq11_pick_del_balance[{i}]")

# (12) Rekkefølge: Levering må skje etter pickup
for i in Np:
    del_node = n + i
    if (i, del_node) in A:
        m.addConstr(
            t[i] + D[i][del_node] - t[del_node] <= 0.0,
            name=f"eq12_pick_before_delivery[{i}]"
        )
    else:
        m.addConstr(
            t[del_node] - t[i] >= 0.0,
            name=f"eq12_pick_before_delivery_weak[{i}]"
        )

os.makedirs("logs", exist_ok=True)
m.Params.TimeLimit = 3600
m.Params.MIPFocus = 1
m.Params.Presolve = 2
m.Params.Cuts = 2
m.Params.Heuristics = 0.25
m.Params.MIPGap = 1e-4
m.Params.Threads = 0
m.Params.LogFile = "logs/PDP-log-MartinAndreassen.txt"
m.Params.OutputFlag = 1

m.optimize()

with open("PDP-solution-MartinAndreassen.txt", "w", encoding="utf-8") as f:
    f.write("PDP Løsning\n")
    f.write("=" * 60 + "\n")
    f.write(f"Status: {m.Status}\n")
    
    if m.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        if m.Status == GRB.OPTIMAL:
            f.write("[OK] Optimal løsning funnet!\n")
        elif m.Status == GRB.TIME_LIMIT:
            f.write("[INFO] Tidsgrense nådd, beste funnet løsning rapportert.\n")
        else:
            f.write("[INFO] Beste gjennomførbare løsning rapportert.\n")
        
        f.write(f"Målverdi: {m.ObjVal:.6f}\n")
        f.write(f"Kjøretid: {m.Runtime:.2f} s\n")
        f.write(f"Antall variabler: {m.NumVars}\n")
        f.write(f"Antall begrensninger: {m.NumConstrs}\n\n")
        
        f.write("Valgte buer (x[i,j]=1):\n")
        f.write("-" * 60 + "\n")
        arcs_used = []
        for (i, j) in A:
            if x[i, j].X > 0.5:
                arcs_used.append((i, j))
                f.write(f"  {i} -> {j}  (distanse: {D[i][j]:.2f})\n")
        
        f.write("\nSpot charter beslutninger (y[i]=1 betyr at pickup i bruker spot charter):\n")
        f.write("-" * 60 + "\n")
        for i in Np:
            if y[i].X > 0.5:
                f.write(f"  Pickup {i}: Bruker spot charter (kostnad: {CS:.2f})\n")
            else:
                f.write(f"  Pickup {i}: Betjent av kjøretøy\n")
        
        f.write("\nTidsvariabler (t[i]):\n")
        f.write("-" * 60 + "\n")
        for i in Nv:
            if i in [o, d]:
                f.write(f"  Node {i} ({'origin' if i == o else 'destinasjon'}): t = {t[i].X:.2f}\n")
            elif i in Np:
                f.write(f"  Node {i} (pickup): t = {t[i].X:.2f}\n")
            elif i in Nd:
                f.write(f"  Node {i} (levering): t = {t[i].X:.2f}\n")
        
        f.write("\nLastvariabler (l[i]):\n")
        f.write("-" * 60 + "\n")
        for i in Nv:
            if i in [o, d]:
                f.write(f"  Node {i} ({'origin' if i == o else 'destinasjon'}): l = {l[i].X:.2f}\n")
            elif i in Np:
                f.write(f"  Node {i} (pickup): l = {l[i].X:.2f} (last +{Q[i]:.2f})\n")
            elif i in Nd:
                pickup_for_del = i - n
                f.write(f"  Node {i} (levering av pickup {pickup_for_del}): l = {l[i].X:.2f} (last -{Q[pickup_for_del]:.2f})\n")
    else:
        f.write(f"[FEIL] Optimalisering feilet med status: {m.Status}\n")
        if m.Status == GRB.INFEASIBLE:
            f.write("Modellen er ikke gjennomførbar. Sjekk begrensninger og data.\n")
        elif m.Status == GRB.UNBOUNDED:
            f.write("Modellen er ubegrenset. Sjekk målfunksjon.\n")

