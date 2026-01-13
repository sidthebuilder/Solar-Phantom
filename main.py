import aerosandbox as asb
import aerosandbox.numpy as np

def design_drone():
    # 1. Define the Geometry
    # ----------------------
    # We are building a "Solar Phantom" - high aspect ratio, lightweight.
    
    airplane = asb.Airplane(
        name="Solar Phantom",
        xyz_ref=[0, 0, 0], # Center of gravity (roughly)
        wings=[
            asb.Wing(
                name="Main Wing",
                symmetric=True, # It mirrors across the center
                x_le=0,         # Leading edge starts at x=0
                ysymmetric=True,
                chord_plot=0.2, # For visualization
                sections=[ # Define the shape from root to tip
                    asb.WingSection(
                        name="Root",
                        y_le=0,
                        chord=1.2,
                        twist=0,
                        airfoil=asb.Airfoil("naca4412") # High lift airfoil
                    ),
                    asb.WingSection(
                        name="Mid",
                        y_le=2.5,
                        chord=1.0,
                        twist=0,
                        airfoil=asb.Airfoil("naca4412")
                    ),
                    asb.WingSection(
                        name="Tip",
                        y_le=6.0, # 12 meter wingspan!
                        chord=0.6,
                        twist=-2, # Washout to prevent tip stall
                        airfoil=asb.Airfoil("naca4412")
                    ),
                ]
            ),
            asb.Wing(
                name="Horizontal Stabilizer",
                symmetric=True,
                x_le=5.5, # Placed far back
                ysymmetric=True,
                chord_plot=0.1,
                sections=[
                    asb.WingSection(
                        name="Root",
                        y_le=0,
                        chord=0.6,
                        airfoil=asb.Airfoil("naca0012")
                    ),
                    asb.WingSection(
                        name="Tip",
                        y_le=1.5,
                        chord=0.4,
                        airfoil=asb.Airfoil("naca0012")
                    )
                ]
            ),
            asb.Wing(
                name="Vertical Stabilizer",
                symmetric=False,
                x_le=5.5,
                ysymmetric=False,
                chord_plot=0.1,
                sections=[
                     asb.WingSection(
                        name="Root",
                        y_le=0,
                        chord=0.7,
                        airfoil=asb.Airfoil("naca0012")
                    ),
                    asb.WingSection(
                        name="Tip",
                        y_le=0, # Vertical
                        z_le=1.0, # Height
                        chord=0.4,
                        airfoil=asb.Airfoil("naca0012")
                    )
                ]
            )
        ],
        fuselages=[
            asb.Fuselage(
                name="Body",
                x_le=-0.5,
                sections=[
                    asb.FuselageSection(x_le=-0.5, width=0.1, height=0.1),
                    asb.FuselageSection(x_le=0.5, width=0.2, height=0.2), # Payload area
                    asb.FuselageSection(x_le=6.0, width=0.05, height=0.05), # Tail boom
                ]
            )
        ]
    )

    return airplane

if __name__ == "__main__":
    # Create the drone
    my_drone = design_drone()
    
    print(f"Designed: {my_drone.name}")
    print(f"Wingspan: {my_drone.wings[0].span():.2f} meters")
    print(f"Mean Aerodynamic Chord: {my_drone.wings[0].mean_aerodynamic_chord():.2f} meters")

    # Visualize it
    # note: This will open a window on your computer
    my_drone.draw_three_view()
    my_drone.draw_wireframe()
