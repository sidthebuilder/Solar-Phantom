import sys
import os
# Force local library usage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import power_solar
import matplotlib.pyplot as plt
import datetime

def check_feasibility_on_day(day_of_year, latitude=20.0):
    """
    Checks if perpetual flight is possible on a specific day.
    Returns: Battery Energy Margin (J) at end of night.
             (Positive = Surplus, Negative = Crash)
    """
    opti = asb.Opti()

    # Fixed Design (Assume we built the optimized drone)
    # These values come from a "Standard" optimization run
    wingspan = 35.0  # m
    total_weight = 150.0 # kg
    battery_mass = 50.0 # kg
    energy_density = 350.0 # Wh/kg (Current Tech)
    payload_power = 30.0 # W (Radio + Avionics)
    
    # Aerodynamics
    # L = W
    velocity = 18.0 # m/s (Cruise)
    q = 0.5 * 1.225 * velocity ** 2
    wing_area = wingspan ** 2 / 25.0 # AR 25
    
    CD0 = 0.02
    e = 0.9
    CL = (total_weight * 9.81) / (q * wing_area)
    k = 1 / (np.pi * e * 25.0)
    CD = CD0 + k * CL ** 2
    drag = CD * q * wing_area
    power_propulsion = (drag * velocity) / 0.70 # Prop efficiency
    
    total_power_out = power_propulsion + payload_power

    # Solar Input for THIS Day
    N = 50
    time = np.linspace(0, 86400, N)
    
    fluxes = power_solar.solar_flux(
        latitude=latitude,
        day_of_year=day_of_year,
        time=time,
        panel_tilt_angle=0
    )
    
    # System Efficiency
    # Panel (22%) * Fill (90%) * MPPT (96%) = ~19%
    power_in = fluxes * wing_area * 0.19 
    
    # Battery Simulation
    max_energy_J = battery_mass * energy_density * 3600
    current_energy = max_energy_J / 2 # Start at 50%
    min_energy_seen = max_energy_J 
    
    dt = 86400 / (N - 1)
    
    # Simple Euler Integration
    for i in range(N):
        net = power_in[i] - total_power_out
        current_energy += net * dt
        
        # Cap at max (cannot overcharge)
        if current_energy > max_energy_J:
            current_energy = max_energy_J
            
        # Track minimum point
        if current_energy < min_energy_seen:
            min_energy_seen = current_energy
            
    return min_energy_seen # If this is < 0, we crashed.

if __name__ == "__main__":
    print("Running Year-Round Survival Analysis...")
    print("Configuration: 35m Span, 150kg Mass, 350 Wh/kg Battery")
    print("-" * 50)
    
    days = np.arange(1, 366)
    margins = []
    latitude = 20.0 # India / Hawaii / Mexico
    
    print(f"Simulating operation at {latitude} degrees Latitude...")
    
    for day in days:
        margin_J = check_feasibility_on_day(day, latitude)
        margin_kWh = margin_J / 3.6e6
        margins.append(margin_kWh)
        
    # Plotting
    margins = np.array(margins)
    
    # Determine Operational Window
    operational_days = days[margins > 0]
    if len(operational_days) > 0:
        start_day = operational_days[0]
        end_day = operational_days[-1]
        
        # Convert to dates
        start_date = (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=int(start_day)-1)).strftime("%b %d")
        end_date = (datetime.datetime(2025, 1, 1) + datetime.timedelta(days=int(end_day)-1)).strftime("%b %d")
        status_msg = f"Operational Window: {start_date} to {end_date}"
    else:
        status_msg = "Operational Window: NONE (Infeasible Year-Round)"

    plt.figure(figsize=(10, 6))
    
    # Color code
    plt.fill_between(days, margins, 0, where=(margins>0), color='green', alpha=0.3, label="Survives Night")
    plt.fill_between(days, margins, 0, where=(margins<=0), color='red', alpha=0.3, label="Crashes")
    
    plt.plot(days, margins, color='black', linewidth=1)
    plt.axhline(0, color='black', linewidth=2)
    
    # Month ticks
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
