# calculations.py
# This file contains all the media calculation logic.

from vessel_data import get_vessel_volume
import math


# ============================================================
# HELPER FUNCTION: CUSTOM ROUNDING RULE
# ============================================================
def smart_round(value: float) -> int:
    """
    Rounding rule: .5 and above rounds UP, below .5 rounds DOWN.
    """
    decimal_part = value - math.floor(value)
    if decimal_part >= 0.5:
        return math.ceil(value)
    else:
        return math.floor(value)


# ============================================================
# SAND MEDIA CALCULATION
# ============================================================
SAND_FREEBOARD = 0.30
SAND_DENSITY = 1.56
SAND_BAG_SIZE = 50


def calculate_sand(model: str, extra_bags: int = 0) -> dict:
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - SAND_FREEBOARD)
    mass = effective_volume * SAND_DENSITY
    raw_bags = mass / SAND_BAG_SIZE
    total_bags = smart_round(raw_bags)
    
    if total_bags == 0:
        grade_a, grade_b, grade_c, grade_d = 0, 0, 0, 0
    elif total_bags == 1:
        grade_a = 1
        grade_b = 0
        grade_c = 0
        grade_d = 0
    elif total_bags == 2:
        grade_a = 1
        grade_b = 1
        grade_c = 0
        grade_d = 0
    elif total_bags <= 6:
        grade_a = 1
        grade_c = 1
        grade_b = total_bags - 2
        grade_d = 0
    elif total_bags <= 9:
        grade_a = 2
        grade_c = 1
        grade_b = total_bags - 3
        grade_d = 0
    elif total_bags == 10:
        grade_a = 3
        grade_b = 5
        grade_c = 1
        grade_d = 1
    else:
        grade_a = round(total_bags * 0.25)
        grade_b = round(total_bags * 0.50)
        grade_c = round(total_bags * 0.15)
        grade_d = round(total_bags * 0.10)
        current_total = grade_a + grade_b + grade_c + grade_d
        difference = total_bags - current_total
        grade_b += difference
    
    grade_b += extra_bags
    
    layering = []
    if grade_d > 0:
        layering.append({"media": "Grade D", "bags": grade_d, "position": "bottom"})
    if grade_c > 0:
        layering.append({"media": "Grade C", "bags": grade_c, "position": "middle"})
    if grade_b > 0:
        b_half = grade_b / 2
        layering.append({"media": "Grade B (bottom)", "bags": round(b_half, 1), "position": "bottom"})
    if grade_a > 0:
        layering.append({"media": "Grade A", "bags": grade_a, "position": "middle"})
    if grade_b > 0:
        b_half = grade_b / 2
        layering.append({"media": "Grade B (top)", "bags": round(b_half, 1), "position": "top"})
    
    return {
        "vessel_model": model,
        "vessel_volume_L": round(volume, 1),
        "effective_volume_L": round(effective_volume, 1),
        "mass_kg": round(mass, 2),
        "raw_bags": round(raw_bags, 2),
        "total_bags": total_bags,
        "grade_a": grade_a,
        "grade_b": grade_b,
        "grade_c": grade_c,
        "grade_d": grade_d,
        "extra_b_for_other_vessels": extra_bags,
        "layering": layering,
    }


# ============================================================
# SUPPORT SAND CALCULATION (for A.C., Resin, Alumina vessels)
# ============================================================
SUPPORT_SAND_RATIO = 0.20


def calculate_support_sand_grades(model: str, freeboard: float = 0.40) -> dict:
    """
    Calculate the Grade B and Grade C sand bags needed to support a vessel,
    split for layering:
        - 50% Grade C (bottom support)
        - 25% Grade B (middle, below main media)
        - 25% Grade B (top, above main media)
    """
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - freeboard)
    sand_volume = effective_volume * SUPPORT_SAND_RATIO
    sand_mass = sand_volume * SAND_DENSITY
    raw_bags = sand_mass / SAND_BAG_SIZE
    total_bags = smart_round(raw_bags)
    
    grade_c_bottom = smart_round(total_bags * 0.50)
    grade_b_middle = smart_round(total_bags * 0.25)
    grade_b_top = total_bags - grade_c_bottom - grade_b_middle
    if grade_b_top < 0:
        grade_b_top = 0
    
    return {
        "total_bags": total_bags,
        "grade_c_bottom": grade_c_bottom,
        "grade_b_middle": grade_b_middle,
        "grade_b_top": grade_b_top,
    }


# ============================================================
# SHARED SUPPORT BAGS CALCULATION
# ============================================================
def calculate_shared_support_bags(num_support_vessels: int, total_extra_bags: int = 2) -> float:
    """
    For small vessels, the +2 extra bags are split equally across all support vessels.
    
    Returns the amount of Grade B per support vessel (float).
    """
    if num_support_vessels <= 0:
        return 0.0
    return total_extra_bags / num_support_vessels


# ============================================================
# ACTIVATED CARBON (A.C.) CALCULATION
# ============================================================
AC_FREEBOARD = 0.40
AC_DENSITY = 0.54
AC_BAG_SIZE = 25
AC_SAND_RATIO = 0.20
AC_MIN_BAGS = 1


def calculate_activated_carbon(model: str, use_extra_sand: bool = False) -> dict:
    """
    Calculate Activated Carbon media, with support sand layering.
    
    Parameters:
        model: Vessel model
        use_extra_sand: If True, sand comes from +2 extra bags (small vessel)
                        If False, sand is calculated separately (large vessel)
    """
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - AC_FREEBOARD)
    sand_volume = effective_volume * AC_SAND_RATIO
    ac_volume = effective_volume * (1 - AC_SAND_RATIO)
    
    ac_mass = ac_volume * AC_DENSITY
    ac_raw_bags = ac_mass / AC_BAG_SIZE
    ac_bags = smart_round(ac_raw_bags)
    if ac_bags < AC_MIN_BAGS:
        ac_bags = AC_MIN_BAGS
    
    layering = []
    support = calculate_support_sand_grades(model, freeboard=AC_FREEBOARD)
    
    if use_extra_sand:
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (bottom)", "bags": round(support["total_bags"] / 2, 1)})
        layering.append({"media": "Activated Carbon", "bags": ac_bags})
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (top)", "bags": round(support["total_bags"] / 2, 1)})
    else:
        if support["grade_c_bottom"] > 0:
            layering.append({"media": "Grade C (bottom)", "bags": support["grade_c_bottom"]})
        if support["grade_b_middle"] > 0:
            layering.append({"media": "Grade B (middle)", "bags": support["grade_b_middle"]})
        layering.append({"media": "Activated Carbon", "bags": ac_bags})
        if support["grade_b_top"] > 0:
            layering.append({"media": "Grade B (top)", "bags": support["grade_b_top"]})
    
    return {
        "vessel_model": model,
        "vessel_volume_L": round(volume, 1),
        "effective_volume_L": round(effective_volume, 1),
        "sand_volume_L": round(sand_volume, 1),
        "sand_bags": support["total_bags"],
        "support_grade_c_bottom": support["grade_c_bottom"],
        "support_grade_b_middle": support["grade_b_middle"],
        "support_grade_b_top": support["grade_b_top"],
        "ac_volume_L": round(ac_volume, 1),
        "ac_mass_kg": round(ac_mass, 2),
        "ac_raw_bags": round(ac_raw_bags, 2),
        "ac_bags": ac_bags,
        "layering": layering,
    }


# ============================================================
# SOFTENER RESIN CALCULATION
# ============================================================
RESIN_FREEBOARD = 0.50
RESIN_DENSITY = 0.83
RESIN_BAG_SIZE = 25
RESIN_SAND_RATIO = 0.20
RESIN_MIN_BAGS = 1


def calculate_resin(model: str, use_extra_sand: bool = False) -> dict:
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - RESIN_FREEBOARD)
    sand_volume = effective_volume * RESIN_SAND_RATIO
    resin_volume = effective_volume * (1 - RESIN_SAND_RATIO)
    
    resin_mass = resin_volume * RESIN_DENSITY
    resin_raw_bags = resin_mass / RESIN_BAG_SIZE
    resin_bags = smart_round(resin_raw_bags)
    if resin_bags < RESIN_MIN_BAGS:
        resin_bags = RESIN_MIN_BAGS
    
    layering = []
    support = calculate_support_sand_grades(model, freeboard=RESIN_FREEBOARD)
    
    if use_extra_sand:
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (bottom)", "bags": round(support["total_bags"] / 2, 1)})
        layering.append({"media": "Resin", "bags": resin_bags})
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (top)", "bags": round(support["total_bags"] / 2, 1)})
    else:
        if support["grade_c_bottom"] > 0:
            layering.append({"media": "Grade C (bottom)", "bags": support["grade_c_bottom"]})
        if support["grade_b_middle"] > 0:
            layering.append({"media": "Grade B (middle)", "bags": support["grade_b_middle"]})
        layering.append({"media": "Resin", "bags": resin_bags})
        if support["grade_b_top"] > 0:
            layering.append({"media": "Grade B (top)", "bags": support["grade_b_top"]})
    
    return {
        "vessel_model": model,
        "vessel_volume_L": round(volume, 1),
        "effective_volume_L": round(effective_volume, 1),
        "sand_volume_L": round(sand_volume, 1),
        "sand_bags": support["total_bags"],
        "support_grade_c_bottom": support["grade_c_bottom"],
        "support_grade_b_middle": support["grade_b_middle"],
        "support_grade_b_top": support["grade_b_top"],
        "resin_volume_L": round(resin_volume, 1),
        "resin_mass_kg": round(resin_mass, 2),
        "resin_raw_bags": round(resin_raw_bags, 2),
        "resin_bags": resin_bags,
        "layering": layering,
    }


# ============================================================
# ACTIVATED ALUMINA CALCULATION
# ============================================================
ALUMINA_FREEBOARD = 0.40
ALUMINA_DENSITY = 0.75
ALUMINA_BAG_SIZE = 25
ALUMINA_SAND_RATIO = 0.20
ALUMINA_MIN_BAGS = 1


def calculate_activated_alumina(model: str, use_extra_sand: bool = False) -> dict:
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - ALUMINA_FREEBOARD)
    sand_volume = effective_volume * ALUMINA_SAND_RATIO
    alumina_volume = effective_volume * (1 - ALUMINA_SAND_RATIO)
    
    alumina_mass = alumina_volume * ALUMINA_DENSITY
    alumina_raw_bags = alumina_mass / ALUMINA_BAG_SIZE
    alumina_bags = smart_round(alumina_raw_bags)
    if alumina_bags < ALUMINA_MIN_BAGS:
        alumina_bags = ALUMINA_MIN_BAGS
    
    layering = []
    support = calculate_support_sand_grades(model, freeboard=ALUMINA_FREEBOARD)
    
    if use_extra_sand:
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (bottom)", "bags": round(support["total_bags"] / 2, 1)})
        layering.append({"media": "Activated Alumina", "bags": alumina_bags})
        if support["total_bags"] > 0:
            layering.append({"media": "Grade B (top)", "bags": round(support["total_bags"] / 2, 1)})
    else:
        if support["grade_c_bottom"] > 0:
            layering.append({"media": "Grade C (bottom)", "bags": support["grade_c_bottom"]})
        if support["grade_b_middle"] > 0:
            layering.append({"media": "Grade B (middle)", "bags": support["grade_b_middle"]})
        layering.append({"media": "Activated Alumina", "bags": alumina_bags})
        if support["grade_b_top"] > 0:
            layering.append({"media": "Grade B (top)", "bags": support["grade_b_top"]})
    
    return {
        "vessel_model": model,
        "vessel_volume_L": round(volume, 1),
        "effective_volume_L": round(effective_volume, 1),
        "sand_volume_L": round(sand_volume, 1),
        "sand_bags": support["total_bags"],
        "support_grade_c_bottom": support["grade_c_bottom"],
        "support_grade_b_middle": support["grade_b_middle"],
        "support_grade_b_top": support["grade_b_top"],
        "alumina_volume_L": round(alumina_volume, 1),
        "alumina_mass_kg": round(alumina_mass, 2),
        "alumina_raw_bags": round(alumina_raw_bags, 2),
        "alumina_bags": alumina_bags,
        "layering": layering,
    }


# ============================================================
# MIXED BED CALCULATION (Sand + Activated Carbon)
# ============================================================
MIXED_FREEBOARD = 0.40
MIXED_SAND_RATIO = 0.50
MIXED_AC_RATIO = 0.50
MIXED_AC_MIN_BAGS = 1


def calculate_mixed_bed(model: str, extra_bags: int = 0) -> dict:
    volume = get_vessel_volume(model)
    effective_volume = volume * (1 - MIXED_FREEBOARD)
    sand_volume = effective_volume * MIXED_SAND_RATIO
    ac_volume = effective_volume * MIXED_AC_RATIO
    
    sand_mass = sand_volume * SAND_DENSITY
    sand_raw_bags = sand_mass / SAND_BAG_SIZE
    sand_total_bags = smart_round(sand_raw_bags)
    
    if sand_total_bags == 0:
        grade_a, grade_b, grade_c, grade_d = 0, 0, 0, 0
    elif sand_total_bags == 1:
        grade_a = 1
        grade_b = 0
        grade_c = 0
        grade_d = 0
    elif sand_total_bags == 2:
        grade_a = 1
        grade_b = 1
        grade_c = 0
        grade_d = 0
    elif sand_total_bags <= 6:
        grade_a = 1
        grade_c = 1
        grade_b = sand_total_bags - 2
        grade_d = 0
    elif sand_total_bags <= 9:
        grade_a = 2
        grade_c = 1
        grade_b = sand_total_bags - 3
        grade_d = 0
    elif sand_total_bags == 10:
        grade_a = 3
        grade_b = 5
        grade_c = 1
        grade_d = 1
    else:
        grade_a = round(sand_total_bags * 0.25)
        grade_b = round(sand_total_bags * 0.50)
        grade_c = round(sand_total_bags * 0.15)
        grade_d = round(sand_total_bags * 0.10)
        current_total = grade_a + grade_b + grade_c + grade_d
        difference = sand_total_bags - current_total
        grade_b += difference
    
    if sand_total_bags <= 6:
        grade_b += 2
    grade_b += extra_bags
    
    ac_mass = ac_volume * AC_DENSITY
    ac_raw_bags = ac_mass / AC_BAG_SIZE
    ac_bags = smart_round(ac_raw_bags)
    if ac_bags < MIXED_AC_MIN_BAGS:
        ac_bags = MIXED_AC_MIN_BAGS
    
    layering = []
    if grade_d > 0:
        layering.append({"media": "Grade D", "bags": grade_d})
    if grade_c > 0:
        layering.append({"media": "Grade C", "bags": grade_c})
    if grade_b > 0:
        b_half = grade_b / 2
        layering.append({"media": "Grade B (bottom)", "bags": round(b_half, 1)})
    if grade_a > 0:
        layering.append({"media": "Grade A", "bags": grade_a})
    if ac_bags > 0:
        layering.append({"media": "Activated Carbon", "bags": ac_bags})
    if grade_b > 0:
        b_half = grade_b / 2
        layering.append({"media": "Grade B (top)", "bags": round(b_half, 1)})
    
    return {
        "vessel_model": model,
        "vessel_volume_L": round(volume, 1),
        "effective_volume_L": round(effective_volume, 1),
        "sand_volume_L": round(sand_volume, 1),
        "sand_mass_kg": round(sand_mass, 2),
        "sand_total_bags": sand_total_bags,
        "grade_a": grade_a,
        "grade_b": grade_b,
        "grade_c": grade_c,
        "grade_d": grade_d,
        "ac_volume_L": round(ac_volume, 1),
        "ac_mass_kg": round(ac_mass, 2),
        "ac_bags": ac_bags,
        "layering": layering,
    }


# ============================================================
# TOTAL SYSTEM SUMMARY FUNCTION
# ============================================================
def calculate_system_summary(system: dict) -> dict:
    """
    Aggregate all media across the entire system.
    """
    summary = {
        "sand": {"grade_a": 0, "grade_b": 0, "grade_c": 0, "grade_d": 0, "total": 0},
        "ac": {"total": 0},
        "resin": {"total": 0},
        "alumina": {"total": 0},
        "mixed": {"sand_a": 0, "sand_b": 0, "sand_c": 0, "sand_d": 0, "ac": 0},
    }
    
    if system.get("sand"):
        s = system["sand"]
        summary["sand"]["grade_a"] += s["grade_a"]
        summary["sand"]["grade_b"] += s["grade_b"]
        summary["sand"]["grade_c"] += s["grade_c"]
        summary["sand"]["grade_d"] += s["grade_d"]
        summary["sand"]["total"] += s["total_bags"]
    
    if system.get("ac"):
        summary["ac"]["total"] += system["ac"]["ac_bags"]
    
    if system.get("resin"):
        summary["resin"]["total"] += system["resin"]["resin_bags"]
    
    if system.get("alumina"):
        summary["alumina"]["total"] += system["alumina"]["alumina_bags"]
    
    if system.get("mixed"):
        m = system["mixed"]
        summary["mixed"]["sand_a"] += m["grade_a"]
        summary["mixed"]["sand_b"] += m["grade_b"]
        summary["mixed"]["sand_c"] += m["grade_c"]
        summary["mixed"]["sand_d"] += m["grade_d"]
        summary["mixed"]["ac"] += m["ac_bags"]
    
    return summary


# ============================================================
# TEST BLOCK
# ============================================================
if __name__ == "__main__":
    print("=== Sand Media Calculation Test ===\n")
    for model in ["1054", "1354", "1865", "3672", "6364"]:
        result = calculate_sand(model)
        print(f"Vessel {model} ({result['vessel_volume_L']} L):")
        print(f"  Total bags: {result['total_bags']}")
        print(f"  A={result['grade_a']}, B={result['grade_b']}, C={result['grade_c']}, D={result['grade_d']}")
        print()
    
    print("=== Shared Support Bags Test ===\n")
    print(f"  3 support vessels → {calculate_shared_support_bags(3)} bags each")
    print(f"  4 support vessels → {calculate_shared_support_bags(4)} bags each")
    print(f"  2 support vessels → {calculate_shared_support_bags(2)} bags each")
    print()
    
    print("=== Activated Carbon Test (Small Vessel — Simple Layering) ===\n")
    for model in ["1354"]:
        result = calculate_activated_carbon(model, use_extra_sand=True)
        print(f"Vessel {model} ({result['vessel_volume_L']} L):")
        print(f"  A.C. bags: {result['ac_bags']}")
        print(f"  Layering (bottom to top):")
        for layer in result['layering']:
            print(f"    - {layer['media']}: {layer['bags']} bags")
        print()
    
    print("=== Activated Carbon Test (Large Vessel — Full Layering) ===\n")
    for model in ["3672"]:
        result = calculate_activated_carbon(model, use_extra_sand=False)
        print(f"Vessel {model} ({result['vessel_volume_L']} L):")
        print(f"  A.C. bags: {result['ac_bags']}")
        print(f"  Layering (bottom to top):")
        for layer in result['layering']:
            print(f"    - {layer['media']}: {layer['bags']} bags")
        print()
        