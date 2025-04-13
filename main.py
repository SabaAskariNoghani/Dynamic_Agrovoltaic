# Description: This script is the main entry point for the solar panel alignment optimization.
import pandas as pd
import pvlib
from pvlib.location import Location
from utilities import setup_animation, compute_shadow, optimize_panel_angles
import numpy as np
from utilities import figure_one, figure_two, figure_three, figure_four
from utilities import shadow_constraint_hard, optimize_panel_angles_no_constraints
import pickle
import os

# ------------------------------------------
# ⚙️ Mode Selection
# ------------------------------------------
run_optimization_mode = True  # 🔁 Set to False to skip optimization and only visualize

# ------------------------------------------
# 📍 Location and Time Setup
# ------------------------------------------
latitude = 41.1171
longitude = 16.87191
tz = 'Europe/Rome'
bari = Location(latitude, longitude, tz=tz)

# Sunny day
selected_date = '2024-06-21'
times = pd.date_range(start=f'{selected_date} 06:00', end=f'{selected_date} 18:00', freq='5min', tz=tz)

solpos = bari.get_solarposition(times)
valid = solpos['apparent_elevation'] > 0
solpos = solpos[valid]
times = solpos.index
sun_positions = list(zip(solpos['azimuth'].values, solpos['apparent_elevation'].values))

# ------------------------------------------
# ⚖️ Panel and Plant Area Setup
# ------------------------------------------
W, L, H = 5.0, 5.0, 5.0
local_corners = np.array([
    [W / 2, L / 2, 0],
    [W / 2, -L / 2, 0],
    [-W / 2, -L / 2, 0],
    [-W / 2, L / 2, 0]
])

plant_bounds = {
    'pos_x': 4.5,
    'neg_x': -3,
    'pos_y': 10,
    'neg_y': -8
}

MIN_SUN_ALTITUDE_DEG = 35  # Minimum sun altitude for shadow calculations
# MIN_SUN_ALTITUDE_DEG = 10  # Minimum sun altitude for shadow calculations

required_radiation = 75000
# required_radiation = 7820

delta = 0.04  # Step size for alignment target adjustment

# ------------------------------------------
# 🌞 Radiation Estimation Function
# ------------------------------------------
def estimate_radiation(shadow_corners, ghi):
    if np.any(np.isnan(shadow_corners)):
        return ghi  # No shadow = full radiation

    plant_area = (plant_bounds['pos_x'] - plant_bounds['neg_x']) * (plant_bounds['pos_y'] - plant_bounds['neg_y'])
    shadow_poly = shadow_corners[:, :2]
    min_x, max_x = np.min(shadow_poly[:, 0]), np.max(shadow_poly[:, 0])
    min_y, max_y = np.min(shadow_poly[:, 1]), np.max(shadow_poly[:, 1])
    shadow_area = max(0, (max_x - min_x) * (max_y - min_y))
    unshaded_area = max(0, plant_area - shadow_area)
    return (unshaded_area / plant_area) * ghi

# ------------------------------------------
# 🧠 Optimization Routine
# ------------------------------------------
def run_optimization(sun_positions, GHI, constraint_problem, target_alignment_init, delta, required_radiation):
    target_alignment = target_alignment_init
    alignment_history = []
    constraint_penalties = []
    optimal_angles = []

    while target_alignment >= 0:
        optimal_angles = []
        total_plant_radiation = 0
        constraint_penalties_step = []

        for i, (phi_s_deg, alpha_s_deg) in enumerate(sun_positions):
            phi_s = np.radians(phi_s_deg)
            alpha_s = np.radians(alpha_s_deg)
            S = np.array([
                np.cos(alpha_s) * np.cos(phi_s),
                np.cos(alpha_s) * np.sin(phi_s),
                np.sin(alpha_s)
            ])

            if constraint_problem:
                phi_p, alpha_p = optimize_panel_angles(S, alpha_s, local_corners, MIN_SUN_ALTITUDE_DEG, H, plant_bounds, target_alignment)
            else:
                phi_p, alpha_p = optimize_panel_angles_no_constraints(S, alpha_s, local_corners, MIN_SUN_ALTITUDE_DEG, H, plant_bounds, target_alignment)

            optimal_angles.append((phi_p, alpha_p))
            penalty = -shadow_constraint_hard((phi_p, alpha_p), S, plant_bounds, local_corners, H)
            constraint_penalties_step.append(penalty)
            _, shadow_corners = compute_shadow(phi_p, alpha_p, S, local_corners, H)
            total_plant_radiation += estimate_radiation(shadow_corners, GHI[i])

        alignment_history.append((target_alignment, total_plant_radiation))

        if total_plant_radiation >= required_radiation:
            print(f"✅ Target met ({'with' if constraint_problem else 'without'} constraints) at alignment target = {target_alignment:.2f}, total radiation = {total_plant_radiation:.2f}")
            break
        else:
            print(f"⚠️ Not enough radiation ({total_plant_radiation:.2f}), reducing alignment target to {target_alignment - delta:.2f}")
            target_alignment -= delta

    return alignment_history, constraint_penalties_step, optimal_angles

# ------------------------------------------
# 🚀 Run or Load
# ------------------------------------------
if run_optimization_mode:
    # Estimate incoming radiation
    clearsky = bari.get_clearsky(times, model='simplified_solis')
    GHI = clearsky['ghi'].values

    # Quick one-pass runs (no refinement)
    _, _, one_pass_angles_with = run_optimization(sun_positions, GHI, True, 1.0, 0.1, 6000)
    _, _, one_pass_angles_without = run_optimization(sun_positions, GHI, False, 1.0, 0.1, 6000)

    # Full iterative runs
    alignment_history_with, constraint_penalties_with, optimal_angles_with = run_optimization(
        sun_positions, GHI, True, 1.0, delta, required_radiation)
    alignment_history_without, constraint_penalties_without, optimal_angles_without = run_optimization(
        sun_positions, GHI, False, 1.0, delta, required_radiation)

    # Save results
    data_to_save = {
        "solpos": solpos,
        "times": times,
        "one_pass_angles_with": one_pass_angles_with,
        "one_pass_angles_without": one_pass_angles_without,
        "alignment_history_with": alignment_history_with,
        "alignment_history_without": alignment_history_without,
        "required_radiation": required_radiation,
        "optimal_angles_with": optimal_angles_with,
        "optimal_angles_without": optimal_angles_without,
        "sun_positions": sun_positions,
        "local_corners": local_corners,
        "H": H,
        "plant_bounds": plant_bounds
    }

    with open("visualization_data.pkl", "wb") as file:
        pickle.dump(data_to_save, file)

    print("✅ Data saved to 'visualization_data.pkl'.")

else:
    # Load previously saved results
    if not os.path.exists("visualization_data.pkl"):
        raise FileNotFoundError("❌ 'visualization_data.pkl' not found. Set run_optimization_mode = True to generate it first.")

    with open("visualization_data.pkl", "rb") as file:
        data = pickle.load(file)

    solpos = data["solpos"]
    times = data["times"]
    one_pass_angles_with = data["one_pass_angles_with"]
    one_pass_angles_without = data["one_pass_angles_without"]
    alignment_history_with = data["alignment_history_with"]
    alignment_history_without = data["alignment_history_without"]
    required_radiation = data["required_radiation"]
    optimal_angles_with = data["optimal_angles_with"]
    optimal_angles_without = data["optimal_angles_without"]
    sun_positions = data["sun_positions"]
    local_corners = data["local_corners"]
    H = data["H"]
    plant_bounds = data["plant_bounds"]

    print("📂 Loaded data from 'visualization_data.pkl'.")

# ------------------------------------------
# 📊 Visualization
# ------------------------------------------

figure_one(solpos, times, MIN_SUN_ALTITUDE_DEG)
figure_two(one_pass_angles_with, one_pass_angles_without, times)
figure_three(alignment_history_with, required_radiation)
figure_four(one_pass_angles_with, sun_positions, times, local_corners, H, plant_bounds, alphabet='a')
figure_four(one_pass_angles_without, sun_positions, times, local_corners, H, plant_bounds, alphabet='b')

# ------------------------------------------
# 🎥 Animate Final Behavior
# ------------------------------------------
setup_animation(optimal_angles_with, sun_positions, local_corners, H, plant_bounds, times)
setup_animation(optimal_angles_without, sun_positions, local_corners, H, plant_bounds, times)
