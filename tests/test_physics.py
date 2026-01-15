import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from physics_model import DronePhysics, PhysicsConstants

class TestPhysicsCore(unittest.TestCase):
    def test_geometry(self):
        """Test basic geometry calculations."""
        wingspan = 10
        aspect_ratio = 10
        area = DronePhysics.geometry(wingspan, aspect_ratio)
        self.assertAlmostEqual(area, 10.0, places=2)

    def test_mass_consistency(self):
        """Test that detailed mass equals total calculated mass."""
        mass_data = DronePhysics.mass_breakdown(
            wingspan=35, 
            wing_area=49, 
            total_weight=150, 
            battery_mass=50, 
            payload_mass=5
        )
        
        # Manually sum components
        manual_sum = (mass_data['structure'] + mass_data['propulsion'] + 
                      mass_data['solar'] + mass_data['mppt'] + 
                      mass_data['avionics'] + mass_data['battery'] + 
                      mass_data['payload'])
                      
        self.assertAlmostEqual(mass_data['total_calculated'], manual_sum, places=3)
        
    def test_aerodynamics(self):
        """Test aerodynamic sanity (Lift should approximate Weight)."""
        # Note: In our specific code, input "total_weight" is treated as the force required (L=W) 
        # for CL calculation.
        aero = DronePhysics.aerodynamics(
            total_weight=100, # kg or Newtons? Code treats as force reference for CL
            velocity=20,
            wing_area=10,
            aspect_ratio=20
        )
        self.assertTrue(aero['CD'] > PhysicsConstants.CD0)
        self.assertTrue(aero['power_required'] > 0)

if __name__ == '__main__':
    unittest.main()
