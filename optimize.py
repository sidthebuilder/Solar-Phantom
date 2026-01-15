import sys
import os
import json
import argparse
import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerosandbox as asb
import aerosandbox.numpy as np
from physics_model import DronePhysics, PhysicsConstants

def optimize_drone(payload_mass=5.0, target_lat=20, min_battery_density=350):
    # 1. Initialize the Optimization Problem
    opti = asb.Opti()

    # 2. Define Variables
    wingspan = opti.variable(init_guess=35, lower_bound=10, upper_bound=80) 
    aspect_ratio = opti.variable(init_guess=20, lower_bound=10, upper_bound=40)
    total_weight = opti.variable(init_guess=100, lower_bound=10, upper_bound=600)
    battery_mass = opti.variable(init_guess=30, lower_bound=5, upper_bound=300)
    velocity = opti.variable(init_guess=20, lower_bound=10, upper_bound=50)

    # 3. Geometric Relations & Physics
    wing_area = DronePhysics.geometry(wingspan, aspect_ratio)
    
    # Mass Breakdown
    mass_data = DronePhysics.mass_breakdown(
        wingspan, wing_area, total_weight, battery_mass, payload_mass
    )
    
    # Enforce Mass Consistency
    opti.subject_to([
        total_weight >= mass_data["total_calculated"]
    ])

    # Aerodynamics
    aero_data = DronePhysics.aerodynamics(
        total_weight, velocity, wing_area, aspect_ratio
    )
    
    # Power Output
    power_draw_motor = aero_data["power_required"] / PhysicsConstants.propulsive_eff
    power_draw_avionics = 50 
    total_power_out = power_draw_motor + power_draw_avionics

    # 4. Solar Energy Model
    day_of_year = 172 # Summer Solstice
    N = 50
    time = np.linspace(0, 86400, N)
    
    power_in_solar = DronePhysics.solar_power_in(
        target_lat, day_of_year, time, wing_area
    )
    
    # 5. Energy Balance
    battery_capacity_Wh_kg = min_battery_density
    max_battery_energy_Joule = battery_mass * battery_capacity_Wh_kg * 3600
    
    init_energy_guess = 50 * 350 * 3600 / 2 
    energy_stored = opti.variable(init_guess=init_energy_guess, n_vars=N)
    
    dt = 86400 / (N - 1)
    
    for i in range(N-1):
        power_net = power_in_solar[i] - total_power_out
        opti.subject_to([
            energy_stored[i+1] == energy_stored[i] + power_net * dt
        ])
        
    opti.subject_to([
        energy_stored >= 0,
        energy_stored <= max_battery_energy_Joule,
        energy_stored[0] == energy_stored[-1]
    ])

    # 6. Optimization Goal
    opti.minimize(total_weight)

    # 7. Solve
    try:
        sol = opti.solve(verbose=False)
    except RuntimeError:
        return None, None
        
    # Pack simplified result object
    result = {
        "sol": sol,
        "wingspan": sol.value(wingspan),
        "total_weight": sol.value(total_weight),
        "battery_mass": sol.value(battery_mass),
        "velocity": sol.value(velocity),
        "aspect_ratio": sol.value(aspect_ratio),
        "time": time,
        "energy": sol.value(energy_stored),
        "max_energy": sol.value(max_battery_energy_Joule),
        "payload": payload_mass,
        "lat": target_lat
    }
    return result

def generate_report(result, filename="simulation_report.md"):
    with open(filename, "w") as f:
        f.write("# Solar Phantom Simulation Report\n\n")
        f.write(f"**Date**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        f.write("## 1. Mission Parameters\n")
        f.write(f"- **Target Latitude**: {result['lat']} deg N\n")
        f.write(f"- **Payload To Carry**: {result['payload']} kg\n\n")
        
        f.write("## 2. Optimized Aircraft Design\n")
        f.write(f"- **Wingspan**: {result['wingspan']:.2f} m\n")
        f.write(f"- **Total Weight**: {result['total_weight']:.2f} kg\n")
        f.write(f"- **Battery Mass**: {result['battery_mass']:.2f} kg\n")
        f.write(f"- **Cruise Speed**: {result['velocity']:.2f} m/s\n\n")
        
        f.write("## 3. Feasibility\n")
        f.write("**VERDICT**: PERPETUAL FLIGHT POSSIBLE\n")
        f.write("The design successfully balances solar collection with power consumption for 24-hour survival.\n")
    
    print(f"Report generated: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize a Solar Drone for Perpetual Flight")
    parser.add_argument("--payload", type=float, default=5.0, help="Payload mass in kg")
    parser.add_argument("--lat", type=float, default=20.0, help="Target latitude in degrees")
    parser.add_argument("--tech", type=float, default=350.0, help="Battery energy density in Wh/kg")
    
    args = parser.parse_args()

    print(f"Optimizing for {args.payload}kg payload at {args.lat}N...")
    
    result = optimize_drone(
        payload_mass=args.payload, 
        target_lat=args.lat,
        min_battery_density=args.tech
    )
        
    if result is None:
        print("\n" + "!" * 50)
        print("PHYSICS LIMIT REACHED: Perpetual Flight Infeasible for these inputs.")
        sys.exit(1)

    print("-" * 50)
    print(f"OPTIMIZATION SUCCESSFUL")
    print(f"Wingspan: {result['wingspan']:.2f} m")
    print(f"Weight  : {result['total_weight']:.2f} kg")
    print("-" * 50)

    # Save Design to JSON (for other scripts)
    design_specs = {
        "wingspan": result['wingspan'],
        "aspect_ratio": result['aspect_ratio'],
        "total_weight": result['total_weight'],
        "battery_mass": result['battery_mass'],
        "velocity": result['velocity'],
        "payload_mass": result['payload'],
        "energy_density": args.tech
    }
    
    with open("design_specs.json", "w") as f:
        json.dump(design_specs, f, indent=4)
        print("Design specifications saved to 'design_specs.json'")
        
    # Generate Report
    generate_report(result)

    # Plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    
    E_kWh = result['energy'] / 3.6e6
    E_max_kWh = result['max_energy'] / 3.6e6
    t_hours = result['time'] / 3600
    
    plt.plot(t_hours, E_kWh, label="Battery Energy", linewidth=2, color="#f39c12")
    plt.axhline(y=E_max_kWh, color='gray', linestyle='--', label="Max Capacity")
    plt.axhline(y=0, color='r', linestyle='-', label="Empty")
    
    plt.xlabel("Time of Day (Hours)")
    plt.ylabel("Energy Stored (kWh)")
    plt.title(f"Perpetual Flight ({args.lat} deg Lat): Battery State")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.fill_between(t_hours, 0, E_kWh, color="#f39c12", alpha=0.1)
    
    print("Plotting mission profile...")
    plt.show()
