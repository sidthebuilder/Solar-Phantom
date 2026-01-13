import sys
import os
# Force local library usage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import power_solar
import matplotlib.pyplot as plt

def solve_for_required_tech(latitude, payload_mass=2.0):
    """
    Solves the Inverse Problem:
    Given a Latitude and Payload, WHAT is the minimum Battery Energy Density (Wh/kg) required?
    """
    opti = asb.Opti()

    # Variables
    wingspan = opti.variable(init_guess=30, lower_bound=10, upper_bound=60)
    aspect_ratio = opti.variable(init_guess=25, lower_bound=15, upper_bound=40)
    total_weight = opti.variable(init_guess=100, lower_bound=5, upper_bound=300) # kg
    battery_mass = opti.variable(init_guess=30, lower_bound=1, upper_bound=150) # kg
    velocity = opti.variable(init_guess=18, lower_bound=10, upper_bound=40) # m/s
    
    # The Magic Variable: Required Tech Level
    required_battery_density = opti.variable(init_guess=350, lower_bound=100, upper_bound=1000) # Wh/kg

    # Geometry
    wing_area = wingspan ** 2 / aspect_ratio
    
    # Mass Model (MPPT Added)
    # Structure (Carbon)
    mass_structure = 0.06 * (wingspan ** 2.45) # Slightly refined structural model
    
    # MPPT Mass Model (from Studies)
    # Estimated Peak Power ~ 1000W -> Mass ~ 0.06 * 1000^0.5 ~= 2kg
    # Simplified for optimization stability:
    mass_mppt = 2.0 
    
    mass_avionics = 1.0 # Autopilot
    mass_propulsion = 0.15 * total_weight
    mass_solar_cells = 0.35 * wing_area
    
    opti.subject_to([
        total_weight / 9.81 >= (mass_structure + payload_mass + mass_avionics + mass_mppt + mass_propulsion + mass_solar_cells + battery_mass)
    ])

    # Aerodynamics
    CD0 = 0.018 # Very clean
    e = 0.92
    
    lift = total_weight
    q = 0.5 * 1.225 * velocity ** 2
    CL = lift / (q * wing_area)
    k = 1 / (np.pi * e * aspect_ratio)
    CD = CD0 + k * CL ** 2
    drag = CD * q * wing_area
    
    power_required = drag * velocity
    propaps_eff = 0.70 # Prop + Motor + ESC
    power_draw = power_required / propaps_eff + 30 # 30W avionics/radio

    # Solar & Energy
    day_of_year = 172 # Summer Solstice (Best Case)
    N = 40
    time = np.linspace(0, 86400, N)
    
    fluxes = power_solar.solar_flux(
        latitude=latitude,
        day_of_year=day_of_year,
        time=time,
        panel_tilt_angle=0
    )
    
    # Panel Eff (24%) * Fill Factor (90%) * MPPT Eff (96%) = ~20%
    sys_solar_eff = 0.20
    power_in = fluxes * wing_area * sys_solar_eff
    
    # Energy Balance
    # Total Energy Stored = Mass * Density
    max_energy_J = battery_mass * required_battery_density * 3600
    
    # Initial guess
    energy = opti.variable(init_guess=1e7, n_vars=N)
    
    dt = 86400 / (N - 1)
    
    for i in range(N-1):
        net_power = power_in[i] - power_draw
        opti.subject_to(energy[i+1] == energy[i] + net_power * dt)
        
    opti.subject_to([
        energy >= 0,
        energy <= max_energy_J,
        energy[0] == energy[-1] # Perpetual
    ])
    
    # OBJECTIVE: Minimize the Required Tech Level
    # We want to find the "Easiest" tech that solves the problem
    opti.minimize(required_battery_density)
    
    try:
        sol = opti.solve(verbose=False)
        return sol.value(required_battery_density)
    except:
        return None

if __name__ == "__main__":
    print("Running Enterprise Technology Boundary Analysis...")
    print("Payload: 2.0 kg (Radio)")
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
    
    print("\nanalysis Complete. Improving Strategic Insight...")
    plt.show()
