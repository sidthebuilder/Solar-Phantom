# Project: Solar Phantom (Forever Drone)

This project aims to design a solar-powered unmanned aerial vehicle (UAV) capable of continuous multi-day flight (Perpetual Flight).

It uses **Multidisciplinary Design Optimization (MDO)** to mathematically prove that the design can sustain energy balance over a 24-hour cycle.

## Built With
*   [AeroSandbox](https://github.com/peterdsharpe/AeroSandbox) - Optimization & Physics Engine

## Key Files
*   `main.py`: **The View**. This script defines the 3D geometry of the aircraft (12m - 30m wingspan high-aspect-ratio glider).
*   `optimize.py`: **The Brain**. This script solves a system of non-linear equations to find the *optimal* aircraft parameters.
    *   **Objective**: Minimize Total Mass.
    *   **Constraints**:
        *   Lift = Weight
        *   Battery State-of-Charge > 0% at all times (24h simulation).
        *   Cyclic Energy Balance (Start Energy = End Energy).
    *   **Physics**: Uses `aerosandbox.library.power_solar` for accurate variable-latitude solar flux modeling.

## How to Run

### 1. Visualization (See the Plane)
```bash
python main.py
```

### 2. Run the Optimization (Solve the Engineering Problem)
```bash
python optimize.py
```
*Output*: Will print the optimal wingspan, battery mass, and cruise speed, and generate a plot showing the battery energy curve over a full day/night cycle.
