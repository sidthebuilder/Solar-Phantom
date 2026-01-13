# Solar Phantom: Perpetual Flight Initiative

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Status: In Development](https://img.shields.io/badge/Status-Building-orange.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)

A high-fidelity **Multidisciplinary Design Optimization (MDO)** framework for determining the physics limits of solar-powered unmanned aerial vehicles (UAVs).

This project uses non-linear optimization to solve the "Perpetual Flight" problem: finding the exact aircraft configuration required to stay airborne indefinitely by balancing solar energy capture with aerodynamic drag and battery storage.

## Key Capabilities

### 1. Physics-Based Optimization (`optimize.py`)
Solves for the optimal aircraft geometry to minimize mass while ensuring 24-hour energy survival.
*   **Input**: Latitude, Payload Mass, Battery Energy Density.
*   **Physics**: Full aerodynamic drag polar estimation + Solar Flux integration.
*   **Result**: Mathematically optimal Wingspan, Battery Mass, and Cruise Speed.

### 2. Technology Boundary Analysis (`analysis_enterprise.py`)
Solves the inverse problem to generate a strategic technology roadmap.
*   **Question**: "What battery technology is required to fly at 50° Latitude?"
*   **Output**: A Feasibility Map sweeping from the Equator to the Arctic Circle.

### 3. Annual Operational Window (`analysis_annual.py`)
Simulates flight operations across every day of the year (1-365).
*   **Output**: "Survival Window" plot showing exactly which months flight is possible for a given design.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Solar-Phantom.git
    cd Solar-Phantom
    ```
2.  Install dependencies (requires AeroSandbox):
    ```bash
    pip install aerosandbox[full]
    ```

## Usage

**To view the Aircraft Geometry:**
```bash
python main.py
```

**To Run the Optimization Solver:**
```bash
python optimize.py
```

**To Generate the Global Feasibility Map:**
```bash
python analysis_enterprise.py
```

**To Check Year-Round Survival Dates:**
```bash
python analysis_annual.py
```

## Attribution
Built using the [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox) optimization framework.
