# TSP Assignment 1 - Three Formulations Comparison

This project implements three different mathematical formulations for the Traveling Salesman Problem (TSP) and compares their performance using Gurobi Optimizer.

## 📋 Overview

The project solves TSP using:
1. **MTZ (Miller-Tucker-Zemlin)** - Position-based formulation with tightening
2. **Svestka** - Flow-based formulation with tightened linking constraints
3. **Dantzig-Fulkerson-Johnson (DFJ)** - Subtour elimination using lazy constraints callback

## 🏗️ Project Structure

```
TSP_Assignment1/
├── data/
│   └── NorwayTSP_Data.py          # Input coordinates
├── utils/
│   ├── base_model.py              # Common utilities
│   └── plot_tour.py               # Optional plotting
├── mtz_model.py                   # MTZ formulation
├── svestka_model.py               # Svestka formulation
├── dantzig_model.py               # DFJ formulation with lazy constraints
├── main.py                        # Main script (runs all models)
├── logs/                          # Gurobi log files
└── solutions/                     # Solution files and summary
```

## 🔧 Requirements

- Python 3.13
- Gurobi Optimizer with valid license
- `gurobipy` package
- Optional: `matplotlib` for plotting

### Installation

1. Install Gurobi Optimizer from [gurobi.com](https://www.gurobi.com/downloads/)
2. Get a license (free academic license available)
3. Install Python packages:

```bash
pip install gurobipy
pip install matplotlib  # Optional, for plotting
```

## 📊 Data Format

Edit `data/NorwayTSP_Data.py` to modify city coordinates:

```python
NORWAY_COORDINATES = {
    'City1': (x1, y1),
    'City2': (x2, y2),
    # Add more cities...
}
```

## 🚀 Usage

### Run All Models

```bash
cd TSP_Assignment1
python main.py [YourName]
```

Example:
```bash
python main.py "JohnDoe"
```

### Run Individual Models

```bash
python mtz_model.py
python svestka_model.py
python dantzig_model.py
```

## 📈 Output

### Console Output
- Progress information for each model
- Model statistics (variables, constraints)
- Solution details (objective, runtime, tour)
- Comparison table

### Generated Files

**Logs** (`logs/`):
- `TSP-log-YourName-MTZ.txt`
- `TSP-log-YourName-Svestka.txt`
- `TSP-log-YourName-Dantzig.txt`

**Solutions** (`solutions/`):
- `TSP-solutions-MTZ-YourName.txt`
- `TSP-solutions-Svestka-YourName.txt`
- `TSP-solutions-Dantzig-YourName.txt`
- `summary.txt` - Comparison table

## ⚙️ Model Details

### MTZ Formulation
- **Variables**: Binary arc variables (x_ij) + continuous position variables (u_i)
- **Constraints**: Degree constraints + MTZ subtour elimination
- **Optimizations**:
  - Tightened bounds on u variables
  - Pre-processing to remove long arcs
  - Optimized Gurobi parameters

### Svestka Formulation
- **Variables**: Binary arc variables (x_ij) + continuous flow variables (f_ij)
- **Constraints**: Degree constraints + flow balance + linking constraints
- **Optimizations**:
  - Tightened linking constraints (f_ij <= (n-2)*x_ij for non-zero arcs)
  - Efficient variable creation

### Dantzig (DFJ) Formulation
- **Variables**: Binary arc variables (x_ij) only
- **Constraints**: Degree constraints + lazy subtour elimination
- **Optimizations**:
  - Lazy constraints callback (adds constraints only when needed)
  - Efficient DFS-based subtour detection

## 🎯 Performance Settings

All models use:
- `TimeLimit = 3600` seconds
- `Threads = -1` (all available cores)
- `MIPFocus = 1` (feasibility focus)
- `Presolve = 2` (aggressive)
- `Cuts = 2` (aggressive cutting)
- `Heuristics = 0.25` (25% time on heuristics)
- `MIPGap = 0.0001`

## 📝 Notes

- The models are optimized for runtime performance
- MTZ typically has the most constraints but can be faster for smaller instances
- Svestka adds flow variables but has tighter bounds
- Dantzig starts with fewer constraints (lazy addition) but may need many callbacks

## 🔍 Troubleshooting

**Gurobi License Error**:
- Ensure Gurobi license is properly installed and activated
- Run `grbgetkey` with your license key

**Import Errors**:
- Verify `gurobipy` is installed: `pip install gurobipy`
- Check Python version (3.13 required)

**Out of Memory**:
- Reduce number of cities in input data
- Adjust pre-processing threshold in MTZ model

## 📄 License

This project is for academic/educational purposes.

## 👤 Author

Martin Andreassen

## 📚 References

- Miller, C. E., Tucker, A. W., & Zemlin, R. A. (1960). Integer programming formulation of traveling salesman problems. *Journal of the ACM*, 7(4), 326-329.
- Svestka, J. A. (1977). A continuous variable representation of the TSP. *Mathematical Programming*, 15(1), 211-213.
- Dantzig, G., Fulkerson, R., & Johnson, S. (1954). Solution of a large-scale traveling-salesman problem. *Journal of the operations research society of America*, 2(4), 393-410.

