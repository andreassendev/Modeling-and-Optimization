# Modeling and Optimization

This repository contains assignments for INF170 (Modeling and Optimization) course, implementing various optimization problems using Gurobi Optimizer.

## 📋 Overview

This project includes implementations of classic optimization problems:

1. **TSP Assignment 1** - Traveling Salesman Problem with three different mathematical formulations
2. **PDP Assignment 2** - Pickup & Delivery Problem with exact constraints
3. **Main Report** - R-based analysis and reporting

## 🏗️ Project Structure

```
MA2-INF170/
├── TSP_Assignment1/          # TSP implementations (MTZ, Svestka, Dantzig)
│   ├── data/                 # Input data (Norway coordinates)
│   ├── utils/                # Utility functions
│   ├── logs/                 # Gurobi log files
│   ├── solutions/            # Solution outputs
│   ├── mtz_model.py          # MTZ formulation
│   ├── svestka_model.py      # Svestka formulation
│   ├── dantzig_model.py      # DFJ formulation with lazy constraints
│   └── main.py               # Main script to run all models
│
├── PDP_Assignment2/          # Pickup & Delivery Problem
│   ├── data/                 # Instance data
│   ├── logs/                 # Gurobi log files
│   ├── PDP-data-YourName.py  # Data loader
│   └── PDP-model-YourName.py # PDP model with constraints (1)-(16)
│
├── Main_report.R             # R script for analysis and reporting
├── MA2-INF170.Rproj          # R project file
├── logs/                     # Root-level log files
├── solutions/                # Root-level solution files
└── README.md                 # This file
```

## 🔧 Requirements

### Python Dependencies

- Python 3.10+ (3.13 recommended)
- Gurobi Optimizer with valid license (free academic license available)
- Required Python packages:
  ```bash
  pip install gurobipy>=11.0.0
  pip install matplotlib>=3.7.0  # Optional, for TSP plotting
  ```

### R Dependencies (for reporting)

- R (>= 4.0)
- Required R packages (install via `install.packages()`):
  - Check `Main_report.R` for specific package requirements

### Gurobi Setup

1. Download Gurobi Optimizer from [gurobi.com](https://www.gurobi.com/downloads/)
2. Get a license (free academic license available at [gurobi.com/academia](https://www.gurobi.com/academia/academic-program-and-licenses/))
3. Install Python package:
   ```bash
   pip install gurobipy
   ```
4. Activate license:
   ```bash
   grbgetkey YOUR_LICENSE_KEY
   ```

## 🚀 Quick Start

### TSP Assignment 1

Run all three TSP formulations:

```bash
cd TSP_Assignment1
python main.py YourName
```

Or run individual models:

```bash
python mtz_model.py
python svestka_model.py
python dantzig_model.py
```

**Output:**
- Logs: `logs/TSP-log-YourName-*.txt`
- Solutions: `solutions/TSP-solutions-*-YourName.txt`
- Summary: `solutions/summary.txt`

### PDP Assignment 2

Run the Pickup & Delivery Problem model:

```bash
cd PDP_Assignment2
python PDP-model-YourName.py
```

**Output:**
- Solution: `PDP-solution-YourName.txt` (in parent directory)
- Log: `logs/PDP-log-YourName.txt`

### Main Report

Open and run the R script:

```r
# In R or RStudio
source("Main_report.R")
```

## 📊 Assignment Details

### TSP Assignment 1

Implements three different mathematical formulations for the Traveling Salesman Problem:

1. **MTZ (Miller-Tucker-Zemlin)**: Position-based formulation with tightened bounds
2. **Svestka**: Flow-based formulation with tightened linking constraints
3. **Dantzig-Fulkerson-Johnson (DFJ)**: Subtour elimination using lazy constraints

**Key Features:**
- Optimized Gurobi parameters for performance
- Pre-processing and model tightening
- Comparison of formulation performance
- Visualization support (optional)

See [TSP_Assignment1/README.md](TSP_Assignment1/README.md) for detailed documentation.

### PDP Assignment 2

Implements the Pickup & Delivery Problem with exact constraints (1)-(16) as specified:

- **Objective**: Minimize total distance + spot charter costs
- **Constraints**: Flow balance, capacity, time windows, pickup-delivery pairing
- **Variables**: Binary routing (x_ij), binary spot charter (y_i), continuous load (l_i), continuous time (t_i)

See [PDP_Assignment2/README.md](PDP_Assignment2/README.md) for detailed documentation.

## ⚙️ Configuration

### Gurobi Parameters

Both assignments use optimized Gurobi parameters:

- `TimeLimit = 3600` seconds (1 hour)
- `Threads = -1` (all available cores)
- `MIPFocus = 1` (feasibility focus)
- `Presolve = 2` (aggressive)
- `Cuts = 2` (aggressive cutting)
- `Heuristics = 0.25` (25% time on heuristics)
- `MIPGap = 0.0001` (0.01%)

### Customization

**TSP**: Edit `TSP_Assignment1/data/NorwayTSP_Data.py` to modify city coordinates.

**PDP**: Edit `PDP_Assignment2/data/Instance_PDP.py` to modify instance data.

## 📈 Output Files

### Logs
- `logs/TSP-log-YourName-*.txt` - TSP model logs
- `logs/PDP-log-YourName.txt` - PDP model log
- `TSP_Assignment1/logs/` - Detailed TSP logs
- `PDP_Assignment2/logs/` - Detailed PDP logs

### Solutions
- `solutions/TSP-solutions-*-YourName.txt` - TSP solutions
- `PDP-solution-YourName.txt` - PDP solution
- `TSP_Assignment1/solutions/` - TSP solution files
- `TSP_Assignment1/solutions/summary.txt` - TSP comparison table

## 🔍 Troubleshooting

### Gurobi License Issues

**Error**: "No Gurobi license found"

**Solution**:
1. Ensure Gurobi is installed correctly
2. Activate license: `grbgetkey YOUR_LICENSE_KEY`
3. Check license file location: `%GRB_LICENSE_FILE%` (Windows) or `$GRB_LICENSE_FILE` (Linux/Mac)
4. For academic license, ensure you're using the academic version

### Import Errors

**Error**: "ModuleNotFoundError: No module named 'gurobipy'"

**Solution**:
```bash
pip install gurobipy
# Or if using virtual environment:
# python -m venv venv
# venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
# pip install gurobipy
```

### Memory Issues

**Error**: "Out of memory" or very slow performance

**Solution**:
- Reduce problem size (number of cities/nodes)
- Adjust pre-processing thresholds in models
- Reduce `TimeLimit` for testing
- Close other memory-intensive applications

### R Package Issues

**Error**: R package not found

**Solution**:
```r
# Install missing packages
install.packages("package_name")
```

## 📝 Notes

- All models are optimized for runtime performance
- Results may vary depending on hardware and Gurobi license type
- Academic licenses may have different performance characteristics
- Log files contain detailed optimization information for analysis

## 📚 References

### TSP Formulations

- Miller, C. E., Tucker, A. W., & Zemlin, R. A. (1960). Integer programming formulation of traveling salesman problems. *Journal of the ACM*, 7(4), 326-329.
- Svestka, J. A. (1977). A continuous variable representation of the TSP. *Mathematical Programming*, 15(1), 211-213.
- Dantzig, G., Fulkerson, R., & Johnson, S. (1954). Solution of a large-scale traveling-salesman problem. *Journal of the operations research society of America*, 2(4), 393-410.

### Gurobi Documentation

- [Gurobi Optimization](https://www.gurobi.com/)
- [Gurobi Python API](https://www.gurobi.com/documentation/current/refman/py_python_api_overview.html)
- [Academic License](https://www.gurobi.com/academia/academic-program-and-licenses/)

## 📄 License

This project is for academic/educational purposes as part of the INF170 course.

## 👤 Author

Martin Andreassen

---

For detailed information about each assignment, see the README files in respective directories:
- [TSP_Assignment1/README.md](TSP_Assignment1/README.md)
- [PDP_Assignment2/README.md](PDP_Assignment2/README.md)

