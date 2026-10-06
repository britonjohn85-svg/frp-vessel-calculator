# vessel_data.py
# This file contains the vessel volume lookup table and the fallback formula.

import math

# ============================================================
# VESSEL VOLUME LOOKUP TABLE (in Litres)
# ============================================================
VESSEL_VOLUMES = {
    "1054": 63.8,
    "1248": 78.6,
    "1354": 108.0,
    "1465": 150.0,
    "1865": 250.0,
    "2162": 310.0,
    "2462": 450.0,
    "3072": 710.0,
    "3672": 1020.0,
    "4672": 1840.0,
    "6364": 2500.0,
}


def get_vessel_volume(model: str) -> float:
    """
    Returns the volume of a vessel in litres.
    
    Primary method: Looks up the exact volume from the table.
    Fallback method: Uses the geometric formula with a 0.90 correction factor.
    
    Parameters:
        model (str): The vessel model, e.g., "3672", "1354", "2182"
    
    Returns:
        float: The vessel volume in litres.
    """
    # Clean the input (remove spaces, dashes, "x", etc.)
    model = model.strip().replace("x", "").replace("-", "").replace(" ", "")
    
    # Primary method: Check the lookup table
    if model in VESSEL_VOLUMES:
        return VESSEL_VOLUMES[model]
    
    # Fallback method: Calculate geometrically
    if len(model) == 4:
        try:
            diameter_in = float(model[:2])
            height_in = float(model[2:])
            
            # Convert inches to litres
            radius_in = diameter_in / 2
            volume_cubic_in = math.pi * (radius_in ** 2) * height_in
            volume_litres = volume_cubic_in * 0.016387
            
            # Apply 0.90 correction factor (for domed ends and fill limits)
            corrected_volume = volume_litres * 0.90
            
            return round(corrected_volume, 1)
        except ValueError:
            pass
    
    # If all else fails, return a default
    raise ValueError(f"Could not determine volume for vessel model: {model}")


# ============================================================
# TEST THE FUNCTION
# ============================================================
if __name__ == "__main__":
    print("=== Vessel Volume Test ===")
    
    # Test known vessels
    for model in ["1054", "1354", "3672", "6364"]:
        vol = get_vessel_volume(model)
        print(f"Vessel {model}: {vol} L")
    
    # Test an unknown vessel (fallback formula)
    print("\n=== Fallback Test ===")
    for model in ["2182", "1665", "2472"]:
        vol = get_vessel_volume(model)
        print(f"Vessel {model} (estimated): {vol} L")
        