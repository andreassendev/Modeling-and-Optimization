# INF170 Assignment 2 – Q2 (PDP) (Exact constraints 1–16)

Pickup & Delivery Problem (PDP) implementation with exact constraints (1)-(16) as specified in the assignment.

## 📁 Project Structure

```
PDP_Assignment2/
├── data/
│   └── Instance_PDP.py          # Input data: Nv, Np, Nd, A, D, Q, K, CS, o, d
├── PDP-data-YourName.py         # Data loader and BigM calculation
├── PDP-model-YourName.py        # Model with all constraints (1)–(16) exactly as specified
├── PDP-solution-YourName.txt    # Solution output
├── logs/
│   └── PDP-log-YourName.txt    # Gurobi log file
└── README.md
```

## 🔧 Requirements

- Python 3.x
- Gurobi Optimizer with valid license
- `gurobipy` package

### Installation

```bash
pip install gurobipy
```

## 📊 Data Format

The data file `data/Instance_PDP.py` must contain:

- **Nv**: List/set of all nodes (origin, pickups, deliveries, destination)
- **Np**: List/set of pickup nodes (typically 1..n)
- **Nd**: List/set of delivery nodes (typically n+1..2n, where delivery of pickup i is n+i)
- **A**: Set/list of arcs (i,j) where i != j
- **D**: Distance matrix as dict-of-dict: D[i][j] for all (i,j) in A
- **Q**: Dict with Q[i] for each pickup node i in Np
- **K**: Vehicle capacity (scalar)
- **CS**: Spot charter cost (scalar)
- **o**: Origin node
- **d**: Destination node

## 🚀 Usage

### Run the Model

```bash
cd PDP_Assignment2
python PDP-model-YourName.py
```

### Output Files

- **PDP-solution-YourName.txt**: Solution report with:
  - Objective value
  - Runtime
  - Selected arcs (x[i,j]=1)
  - Spot charter decisions (y[i])
  - Time variables (t[i])
  - Load variables (l[i])

- **logs/PDP-log-YourName.txt**: Detailed Gurobi optimization log

## 📐 Model Constraints

The model implements exactly constraints (1)-(16) as specified:

1. **Objective**: Minimize total distance + spot charter costs
2. **Allocation**: Each pickup is either served or uses spot charter
3. **Origin**: Vehicle leaves origin exactly once
4. **Flow balance**: Inflow = outflow for all intermediate nodes
5. **Destination**: Vehicle enters destination exactly once
6. **Load at pickup**: Load increases when picking up
7. **Load at delivery**: Load decreases when delivering
8. **Load bounds**: 0 ≤ l_i ≤ K
9. **Time from origin**: Time constraints from origin
10. **Time on arcs**: Time constraints on all arcs
11. **Pickup-delivery balance**: Pickup and delivery must be on same route
12. **Pickup before delivery**: Time ordering constraint
13. **Binary y_i**: y_i ∈ {0,1}
14. **Binary x_ij**: x_ij ∈ {0,1}
15. **Non-negative load**: l_i ≥ 0
16. **Non-negative time**: t_i ≥ 0

## ⚙️ Configuration

- **Time Limit**: 3600 seconds (1 hour)
- **MIP Focus**: 1 (feasibility)
- **Presolve**: 2 (aggressive)
- **Cuts**: 2 (aggressive)
- **Heuristics**: 0.25 (25% of time)
- **MIP Gap**: 1e-4 (0.01%)

## 📝 Notes

- The model follows the exact constraint formulation without rewriting inequalities
- BigM is calculated conservatively as `maxD * max(1, |Nv|)`
- All constraints are implemented exactly as specified in the assignment
- The model uses lazy constraints are not needed for this formulation (all constraints are explicit)

## 🔍 Customization

To use your own instance:

1. Edit `data/Instance_PDP.py` with your data
2. Ensure all required variables (Nv, Np, Nd, A, D, Q, K, CS, o, d) are defined
3. Run `python PDP-model-YourName.py`

