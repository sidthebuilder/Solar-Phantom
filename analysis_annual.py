import sys
import os
import json
import datetime
# Force local library usage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
from physics_model import DronePhysics, PhysicsConstants

def load_design():
    """Type-safe loading of design specs."""
    try:
        with open("design_specs.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: 'design_specs.json' not found. Please run 'optimize.py' first.")
        sys.exit(1)

def check_feasibility_on_day(day_of_year, design, latitude=20.0):
    """
    Checks if perpetual flight is possible on a specific day using the optimized design.
    """
    # 1. Unpack Design
    wingspan = design["wingspan"]
    total_weight = design["total_weight"]
    battery_mass = design["battery_mass"]
    velocity = design["velocity"]
    aspect_ratio = design["aspect_ratio"]
    battery_capacity = design["energy_density"]
    
    # 2. Physics Model Calls
    wing_area = DronePhysics.geometry(wingspan, aspect_ratio)
    
    # Aerodynamics
    aero_data = DronePhysics.aerodynamics(
        total_weight, velocity, wing_area, aspect_ratio
    )
    
    # Power Consumption
    # Power = Drag * V / Prop_Eff + Avionics
    power_draw_motor = aero_data["power_required"] / PhysicsConstants.propulsive_eff
    total_power_out = power_draw_motor + PhysicsConstants.mass_avionics * 50 # approximation if avionics power not saved?
    # Note: Optimization used fixed 50W for avionics. Let's start with that constant to match optimize.py 
    # Or better, define it in PhysicsConstants? The constants file has mass, not power.
    # I'll stick to 50W to match optimize.py logic.
    total_power_out = power_draw_motor + 50.0

    # 3. Solar Input for THIS Day
    N = 50
    time = np.linspace(0, 86400, N)
    
    power_in = DronePhysics.solar_power_in(
        latitude, day_of_year, time, wing_area
    )
    
    # 4. Battery Simulation
    max_energy_J = battery_mass * battery_capacity * 3600
    current_energy = max_energy_J / 2 # Start at 50%
    min_energy_seen = max_energy_J 
    
    dt = 86400 / (N - 1)
    
    # Integration
    for i in range(N):
        net = power_in[i] - total_power_out
        current_energy += net * dt
        
        # Cap at max
        if current_energy > max_energy_J:
            current_energy = max_energy_J
            
        # Track minimum
        if current_energy < min_energy_seen:
            min_energy_seen = current_energy
            
    return min_energy_seen

if __name__ == "__main__":
    print("Running Year-Round Survival Analysis...")
    design = load_design()
    print(f"Loaded Design: {design['wingspan']:.2f}m Span, {design['total_weight']:.1f}kg Mass")
    print("-" * 50)
    
    days = np.arange(1, 366)
    margins = []
    latitude = 20.0 
    
    print(f"Simulating operation at {latitude} degrees Latitude...")
    
    for day in days:
        margin_J = check_feasibility_on_day(day, design, latitude)
        margin_kWh = margin_J / 3.6e6
        margins.append(margin_kWh)
        
    # Plotting
    margins = np.array(margins)
    
    operational_days = days[margins > 0]
    if len(operational_days) > 0:
        start_day = operational_days[0]
        end_day = operational_days[-1]
        
        start_date = (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=int(start_day)-1)).strftime("%b %d")
        end_date = (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=int(end_day)-1)).strftime("%b %d")
        status_msg = f"Operational Window: {start_date} to {end_date}"
    else:
        status_msg = "Operational Window: NONE (Infeasible Year-Round)"

    plt.figure(figsize=(10, 6))
    
    plt.fill_between(days, margins, 0, where=(margins>0), color='green', alpha=0.3, label="Survives Night")
    plt.fill_between(days, margins, 0, where=(margins<=0), color='red', alpha=0.3, label="Crashes")
    
    plt.plot(days, margins, color='black', linewidth=1)
    plt.axhline(0, color='black', linewidth=2)
    
    month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    plt.xticks(month_starts, month_names)
    
    plt.title(f"Year-Round Mission Availability (Lat: {latitude}N)\n{status_msg}")
    plt.xlabel("Date")
    plt.ylabel("Energy Margin at Sunrise (kWh)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    print(status_msg)
    plt.show()
