import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import power_solar

def optimize_drone():
    # 1. Initialize the Optimization Problem
    # --------------------------------------
    opti = asb.Opti()

    # 2. Define Variables (The "Knobs")
    # ---------------------------------
    # We let the optimizer choose the best values for these:
    wingspan = opti.variable(init_guess=30, lower_bound=10, upper_bound=80) # meters
    aspect_ratio = opti.variable(init_guess=20, lower_bound=10, upper_bound=40) # Slender wings
    total_weight = opti.variable(init_guess=100, lower_bound=10, upper_bound=600) # kg
    battery_mass = opti.variable(init_guess=30, lower_bound=5, upper_bound=300) # kg
    
    # Flight variable: Cruise speed
    velocity = opti.variable(init_guess=20, lower_bound=10, upper_bound=50) # m/s (approx 72 km/h)

    # 3. Geometric Relations
    # ----------------------
    wing_area = wingspan ** 2 / aspect_ratio
    chord = wingspan / aspect_ratio
    
    # 4. Mass Buildup Model (The Physics of Weight)
    # ---------------------------------------------
    # Structural weight estimates based on historical data for solar aircraft
    # (Simplified for this project)
    # Carbon fiber structure scaling roughly with span^3 (cubic law)
    mass_structure_raw = 0.05 * (wingspan ** 2.5) 
    
    mass_payload = 5.0 # Camera, comms, etc. (kg)
    mass_avionics = 2.0 # Autopilot, servos (kg)
    mass_propulsion = 0.2 * total_weight # Motors, prop, ESC roughly scale with size
    mass_solar_cells = 0.3 * wing_area # approx 0.3 kg/m^2 for flexible solar arrays
    
    # Enforce Mass Consistency
    # Total Weight must equal sum of parts
    opti.subject_to([
        total_weight / 9.81 >= (mass_structure_raw + mass_payload + mass_avionics + mass_propulsion + mass_solar_cells + battery_mass)
    ])

    # 5. Aerodynamics Model (The Physics of Flight)
    # ---------------------------------------------
    # Simple Drag Polar: CD = CD0 + k * CL^2
    CD0 = 0.02 # Parasitic drag coefficient (streamlined laminar body)
    e = 0.9    # Oswald efficiency factor (high efficiency wing)
    
    # Lift Requirement: Lift = Weight
    lift = total_weight # Newtons
    dynamic_pressure = 0.5 * 1.225 * velocity ** 2 # Sea level density for simplicity
    
    CL = lift / (dynamic_pressure * wing_area)
    
    # Induced Drag factor
    k = 1 / (np.pi * e * aspect_ratio)
    
    # Total Drag
    CD = CD0 + k * CL ** 2
    drag = CD * dynamic_pressure * wing_area
    
    # Power required to fly (Output Power)
    power_required_flight = drag * velocity
    
    # Total power consumption (including inefficiencies)
    # Propeller eff (0.85) * Motor eff (0.90) * ESC eff (0.95) ~= 0.72
    propulsive_efficiency = 0.72
    power_draw_motor = power_required_flight / propulsive_efficiency
    power_draw_avionics = 50 # Watts constant draw
    
    total_power_out = power_draw_motor + power_draw_avionics

    # 6. Solar Energy Model (The physics of Power)
    # --------------------------------------------
    # Simulating a day in June (Day 172) at 20 degrees North Latitude
    latitude = 20
    day_of_year = 172
    
    # Discretize the day into N segments
    N = 50
    time = np.linspace(0, 86400, N) # Seconds in a day
    
    # Calculate Solar Flux for each time step
    # We assume wings are horizontal (flat)
    fluxes = power_solar.solar_flux(
        latitude=latitude,
        day_of_year=day_of_year,
        time=time,
        panel_tilt_angle=0
    )
    
    # Solar array efficiency (modern silicon/embedded)
    panel_efficiency = 0.22 
    # Area filling factor (how much of the wing is covered)
    fill_factor = 0.90
    
    power_in_solar = fluxes * wing_area * fill_factor * panel_efficiency
    
    # 7. Energy Balance Simulation (The "Perpetual" Check)
    # ----------------------------------------------------
    # We simulate the battery energy level over the 24 hours.
    # Energy[i+1] = Energy[i] + (Power_In - Power_Out) * dt
    
    battery_capacity_Wh_kg = 350 # High-end Li-Ion pack density
    max_battery_energy_Joule = battery_mass * battery_capacity_Wh_kg * 3600
    
    # Initial guess for battery energy (assuming ~50kg battery initially)
    init_energy_guess = 50 * 350 * 3600 / 2 
    energy_stored = opti.variable(init_guess=init_energy_guess, n_vars=N)
    
    # Constraint: Battery State-of-Charge Dynamics
    dt = 86400 / (N - 1)
    
    for i in range(N-1):
        # Change in energy = (Solar Input - Power Drain) * time
        power_net = power_in_solar[i] - total_power_out
        
        # Euler integration
        opti.subject_to([
            energy_stored[i+1] == energy_stored[i] + power_net * dt
        ])
        
    # Constraints on Battery
    opti.subject_to([
        energy_stored >= 0, # Never run out of power!
        energy_stored <= max_battery_energy_Joule, # Cannot overcharge
        energy_stored[0] == energy_stored[-1] # Perpetual: End state = Start state
    ])

    # 8. Optimization Goal
    # --------------------
    # Minimize the Total Weight (Lightest drone that can fly forever)
    opti.minimize(total_weight)

    # 9. Solve
    # --------
    sol = opti.solve()

    # 10. Output Results
    # ------------------
    print("-" * 50)
    print("OPTIMIZATION SUCCESSFUL: Perpetual Solar Plane Designed")
    print("-" * 50)
    print(f"Total Weight : {sol.value(total_weight):.2f} kg")
    print(f"Wingspan     : {sol.value(wingspan):.2f} m")
    print(f"Aspect Ratio : {sol.value(aspect_ratio):.2f}")
    print(f"Cruise Speed : {sol.value(velocity):.2f} m/s ({sol.value(velocity)*3.6:.1f} km/h)")
    print(f"Battery Mass : {sol.value(battery_mass):.2f} kg ({sol.value(battery_mass)/sol.value(total_weight)*100:.1f}% of total)")
    print("-" * 50)
    
    return sol, time, sol.value(energy_stored), sol.value(max_battery_energy_Joule)

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    try:
        sol, t, E, E_max = optimize_drone()
        
        # Visualize the Mission
        plt.figure(figsize=(10, 6))
        
        # Convert J to kWh for readability
        E_kWh = E / 3.6e6
        E_max_kWh = E_max / 3.6e6
        t_hours = t / 3600
        
        plt.plot(t_hours, E_kWh, label="Battery Energy", linewidth=2, color="#f39c12")
        plt.axhline(y=E_max_kWh, color='gray', linestyle='--', label="Max Capacity")
        plt.axhline(y=0, color='r', linestyle='-', label="Empty")
        
        plt.xlabel("Time of Day (Hours)")
        plt.ylabel("Energy Stored (kWh)")
        plt.title("Perpetual Flight: Battery State over 24 Hours")
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.fill_between(t_hours, 0, E_kWh, color="#f39c12", alpha=0.1)
        
        print("Plotting mission profile...")
        plt.show()
        
    except Exception as e:
        print("Optimization Failed or Unfeasible Configuration!")
        print(e)
