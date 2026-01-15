import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library import power_solar

class PhysicsConstants:
    """Central repository for physical constants to ensure consistency."""
    g = 9.81
    
    # Aerodynamics
    CD0 = 0.018       # Refined parasitic drag coefficient
    oswald_eff = 0.92 # Refined Oswald efficiency factor
    
    # Structures
    # Mass = k * span ^ exp
    struct_mass_coeff = 0.06
    struct_mass_exp = 2.45
    
    # Solar System
    solar_cell_coverage = 0.90 # Fill factor
    solar_cell_eff = 0.22      # Cell efficiency
    mppt_eff = 0.96           # MPPT efficiency
    propulsive_eff = 0.72     # Propeller * Motor * ESC
    
    # Weights
    mass_mppt = 2.0 # kg
    mass_avionics = 1.0 # kg
    mass_solar_density = 0.35 # kg/m^2 (panel + encapsulation)

class DronePhysics:
    @staticmethod
    def geometry(wingspan, aspect_ratio):
        """Calculates derived geometric properties."""
        wing_area = wingspan ** 2 / aspect_ratio
        return wing_area

    @staticmethod
    def mass_breakdown(wingspan, wing_area, total_weight, battery_mass, payload_mass):
        """
        Returns a dictionary of mass components and checks structural constraints.
        """
        # Structural Mass (The main scaling factor)
        mass_structure = PhysicsConstants.struct_mass_coeff * (wingspan ** PhysicsConstants.struct_mass_exp)
        
        mass_propulsion = 0.15 * total_weight # Motors scale with aircraft weight/power
        mass_solar = PhysicsConstants.mass_solar_density * wing_area
        
        total_calculated_mass = (
            mass_structure + 
            mass_propulsion + 
            mass_solar + 
            PhysicsConstants.mass_mppt + 
            PhysicsConstants.mass_avionics + 
            battery_mass + 
            payload_mass
        )
        
        return {
            "structure": mass_structure,
            "propulsion": mass_propulsion,
            "solar": mass_solar,
            "mppt": PhysicsConstants.mass_mppt,
            "avionics": PhysicsConstants.mass_avionics,
            "battery": battery_mass,
            "payload": payload_mass,
            "total_calculated": total_calculated_mass
        }

    @staticmethod
    def aerodynamics(total_weight, velocity, wing_area, aspect_ratio):
        """
        Calculates Drag and Power Required.
        """
        q = 0.5 * 1.225 * velocity ** 2
        lift = total_weight  # Steady level flight, L=W (in Newtons in physics, but here weight often treated as kg in simple models? 
                             # Wait, simple models often mix. Let's be precise.
                             # Input total_weight is usually kg in this project.
                             # Lift needs Newtons.
        
        lift_force = lift * PhysicsConstants.g
        
        CL = lift_force / (q * wing_area)
        
        # Induced Drag
        k = 1 / (np.pi * PhysicsConstants.oswald_eff * aspect_ratio)
        CD = PhysicsConstants.CD0 + k * CL ** 2
        
        drag_force = CD * q * wing_area
        
        power_required_aero = drag_force * velocity
        
        return {
            "CL": CL,
            "CD": CD,
            "drag_force": drag_force,
            "power_required": power_required_aero
        }

    @staticmethod
    def solar_power_in(latitude, day_of_year, time_array, wing_area):
        """
        Calculates solar power input over a time array.
        """
        fluxes = power_solar.solar_flux(
            latitude=latitude,
            day_of_year=day_of_year,
            time=time_array,
            panel_tilt_angle=0
        )
        
        # Net efficiency chain
        net_eff = (PhysicsConstants.solar_cell_eff * 
                   PhysicsConstants.solar_cell_coverage * 
                   PhysicsConstants.mppt_eff)
                   
        return fluxes * wing_area * net_eff
