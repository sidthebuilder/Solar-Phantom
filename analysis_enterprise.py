import sys
import os
# Force local library usage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
from physics_model import DronePhysics, PhysicsConstants

def solve_for_required_tech(latitude, payload_mass=2.0):
    """
    Solves the Inverse Problem:
    Given a Latitude and Payload, WHAT is the minimum Battery Energy Density (Wh/kg) required?
    """
    opti = asb.Opti()

    # Variables
    wingspan = opti.variable(init_guess=30, lower_bound=10, upper_bound=60)
    aspect_ratio = opti.variable(init_guess=25, lower_bound=15, upper_bound=40)
    total_weight = opti.variable(init_guess=100, lower_bound=5, upper_bound=300) 
    battery_mass = opti.variable(init_guess=30, lower_bound=1, upper_bound=150)
    velocity = opti.variable(init_guess=18, lower_bound=10, upper_bound=40)
    
    # The Magic Variable: Required Tech Level
    required_battery_density = opti.variable(init_guess=350, lower_bound=100, upper_bound=1000) # Wh/kg

    # Geometry
    wing_area = DronePhysics.geometry(wingspan, aspect_ratio)
    
    # Mass Model
    # Note: PhysicsConstants.mass_mppt and others are used internally by DronePhysics
    mass_data = DronePhysics.mass_breakdown(
        wingspan, wing_area, total_weight, battery_mass, payload_mass
    )
    
    opti.subject_to([
        total_weight / 9.81 >= mass_data["total_calculated"]
    ])

    # Aerodynamics
    aero_data = DronePhysics.aerodynamics(
        total_weight, velocity, wing_area, aspect_ratio
    )
    
    # Power
    power_draw_motor = aero_data["power_required"] / PhysicsConstants.propulsive_eff
    power_draw_avionics = 30 # Enterprise analysis assumed 30W avionics (radio only) vs 50W full autopilot?
    # Let's standardize to the PhysicsConstants.mass_avionics implies... actually mass != power.
    # The original enterprise script had 30W. optimize.py had 50W.
    # Standardizing to 50W to be safe/consistent with optimize.py
    power_draw_avionics = 50 
    
    total_power_out = power_draw_motor + power_draw_avionics

    # Solar & Energy
    day_of_year = 172 # Summer Solstice 
    N = 40
    time = np.linspace(0, 86400, N)
    
    power_in = DronePhysics.solar_power_in(
        latitude, day_of_year, time, wing_area
    )
    
    # Energy Balance
    # Total Energy Stored = Mass * Density
    max_energy_J = battery_mass * required_battery_density * 3600
    
    # Initial guess
    energy = opti.variable(init_guess=1e7, n_vars=N)
    
    dt = 86400 / (N - 1)
    
    for i in range(N-1):
        net_power = power_in[i] - total_power_out
        opti.subject_to(energy[i+1] == energy[i] + net_power * dt)
        
    opti.subject_to([
        energy >= 0,
        energy <= max_energy_J,
        energy[0] == energy[-1] # Perpetual
    ])
    
    # OBJECTIVE: Minimize the Required Tech Level
    opti.minimize(required_battery_density)
    
    try:
        sol = opti.solve(verbose=False)
        return sol.value(required_battery_density)
    except:
        return None

if __name__ == "__main__":
    print("Running Enterprise Technology Boundary Analysis (Unified Physics)...")
    print("Payload: 2.0 kg (Standardized)")
    print("-" * 40)
    
    latitudes = [0, 10, 20, 30, 40, 50, 60]
    required_tech = []
    
    print(f"{'Lat (deg)':<10} | {'Req. Battery (Wh/kg)':<25} | {'Feasibility'}")
    print("-" * 50)
    
    for lat in latitudes:
        tech = solve_for_required_tech(lat, payload_mass=2.0)
        
        if tech:
            status = "FEASIBLE"
            if tech > 500: status = "FUTURE TECH (2030+)"
            elif tech > 350: status = "NEXT GEN (2026)"
            else: status = "AVAILABLE NOW"
            
            print(f"{lat:<10} | {tech:<25.1f} | {status}")
            required_tech.append(tech)
        else:
            print(f"{lat:<10} | {'Infeasible':<25} | IMPOSSIBLE")
            required_tech.append(None)
            
    # Plotting
    valid_lats = [l for l, t in zip(latitudes, required_tech) if t is not None]
    valid_tech = [t for t in required_tech if t is not None]
    
    plt.figure(figsize=(10, 6))
    plt.plot(valid_lats, valid_tech, 'o-', linewidth=3, color='#2980b9', markersize=8)
    
    # Reference Lines
    plt.axhline(y=250, color='green', linestyle='--', label="Cheap Li-Ion (250 Wh/kg)")
    plt.axhline(y=350, color='orange', linestyle='--', label="High-End Li-Ion (350 Wh/kg)")
    plt.axhline(y=500, color='red', linestyle='--', label="Solid State / Li-S (500 Wh/kg)")
    
    plt.fill_between(valid_lats, 0, 250, color='green', alpha=0.1)
    plt.fill_between(valid_lats, 250, 350, color='orange', alpha=0.1)
    plt.fill_between(valid_lats, 350, 1000, color='red', alpha=0.1)
    
    plt.title(f"Strategic Technology Roadmap: Solar Drone (2kg Payload)\nLatitude Feasibility analysis")
    plt.xlabel("Latitude (Degrees)")
    plt.ylabel("Required Battery Energy Density (Wh/kg)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.ylim(100, 600)
    
    print("\nAnalysis Complete.")
    plt.show()
