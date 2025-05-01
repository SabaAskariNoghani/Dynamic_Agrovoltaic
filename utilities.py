# utilities.py

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D  # Ensures 3D projection registration
from matplotlib.patches import Rectangle
import matplotlib as mpl
from matplotlib.collections import LineCollection
from matplotlib import cm
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
# ------------------------------------------
# Rotation Utilities
# ------------------------------------------
def Rz(phi):
    return np.array([
        [np.cos(phi), -np.sin(phi), 0],
        [np.sin(phi), np.cos(phi), 0],
        [0, 0, 1]
    ])

def Rx(alpha):
    return np.array([
        [1, 0, 0],
        [0, np.cos(alpha), -np.sin(alpha)],
        [0, np.sin(alpha), np.cos(alpha)]
    ])

def composite_rotation(phi, alpha):
    return  Rz(phi) @ Rx(alpha) 

# ------------------------------------------
# Compute Shadow Projection
# ------------------------------------------
def compute_shadow(phi_p, alpha_p, S, local_corners, H):
    R = composite_rotation(phi_p, alpha_p)
    global_corners = (R @ local_corners.T).T + np.array([0, 0, H])

    if S[2] <= 0:
        return global_corners, np.full_like(global_corners, np.nan)

    panel_normal = R @ np.array([0, 0, 1])

    if np.abs(np.dot(panel_normal, S)) < 1e-6:
        shadow_corners = np.zeros((4, 3))
    else:
        shadow_corners = np.array([C - (C[2] / S[2]) * S for C in global_corners])
        shadow_corners[:, 2] = 0

    return global_corners, shadow_corners

# ------------------------------------------
# Visualization: 3D Animation Setup
# ------------------------------------------
def setup_animation(optimal_angles, sun_positions, local_corners, H, plant_bounds, times):
    plant_bound_neg_x = plant_bounds['neg_x']
    plant_bound_pos_x = plant_bounds['pos_x']
    plant_bound_neg_y = plant_bounds['neg_y']
    plant_bound_pos_y = plant_bounds['pos_y']

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    def set_axes_equal(ax):
        x_limits = [plant_bound_neg_x, plant_bound_pos_x]
        y_limits = [plant_bound_neg_y, plant_bound_pos_y]
        z_limits = [0, 6]

        ax.set_xlim(x_limits)
        ax.set_ylim(y_limits)
        ax.set_zlim(z_limits)

        x_range = x_limits[1] - x_limits[0]
        y_range = y_limits[1] - y_limits[0]
        z_range = z_limits[1] - z_limits[0]
        max_range = max(x_range, y_range, z_range)
        ax.set_box_aspect([x_range / max_range, y_range / max_range, z_range / max_range])

    set_axes_equal(ax)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title("3D View: Panel, Sun, and Shadow Projection")

    grid_x = np.linspace(plant_bound_neg_x, plant_bound_pos_x, 10)
    grid_y = np.linspace(plant_bound_neg_y, plant_bound_pos_y, 10)
    Xg, Yg = np.meshgrid(grid_x, grid_y)
    ax.plot_surface(Xg, Yg, np.zeros_like(Xg), color='green', alpha=0.3)

    global panel_poly, shadow_poly
    panel_poly = Poly3DCollection([], facecolors='cyan', alpha=0.5, edgecolor='black')
    shadow_poly = Poly3DCollection([], facecolors='gray', alpha=0.5, edgecolor='black')
    ax.add_collection3d(panel_poly)
    ax.add_collection3d(shadow_poly)

    def update(frame):
        phi_p, alpha_p = optimal_angles[frame]
        phi_s_deg, alpha_s_deg = sun_positions[frame]

        phi_s = np.radians(phi_s_deg)
        alpha_s = np.radians(alpha_s_deg)
        S = np.array([
            np.cos(alpha_s) * np.cos(phi_s),
            np.cos(alpha_s) * np.sin(phi_s),
            np.sin(alpha_s)
        ])

        global_corners, shadow_corners = compute_shadow(phi_p, alpha_p, S, local_corners, H)

        panel_poly.set_verts([global_corners])
        shadow_poly.set_verts([shadow_corners])
        return panel_poly, shadow_poly

    ani = animation.FuncAnimation(fig, update, frames=len(times), interval=100, blit=False)
    plt.show()


def setup_animation1(optimal_angles, sun_positions, local_corners, H, plant_bounds, times):
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
    import matplotlib.animation as animation
    from matplotlib.lines import Line2D

    plant_bound_neg_x = plant_bounds['neg_x']
    plant_bound_pos_x = plant_bounds['pos_x']
    plant_bound_neg_y = plant_bounds['neg_y']
    plant_bound_pos_y = plant_bounds['pos_y']

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    def set_axes_equal(ax):
        x_limits = [plant_bound_neg_x, plant_bound_pos_x]
        y_limits = [plant_bound_neg_y, plant_bound_pos_y]
        z_limits = [0, 6]

        ax.set_xlim(x_limits)
        ax.set_ylim(y_limits)
        ax.set_zlim(z_limits)

        x_range = x_limits[1] - x_limits[0]
        y_range = y_limits[1] - y_limits[0]
        z_range = z_limits[1] - z_limits[0]
        max_range = max(x_range, y_range, z_range)
        ax.set_box_aspect([x_range / max_range, y_range / max_range, z_range / max_range])

    set_axes_equal(ax)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.set_title("3D View: Panel, Sun, Shadow, and Normals")

    # Draw ground
    grid_x = np.linspace(plant_bound_neg_x, plant_bound_pos_x, 10)
    grid_y = np.linspace(plant_bound_neg_y, plant_bound_pos_y, 10)
    Xg, Yg = np.meshgrid(grid_x, grid_y)
    ax.plot_surface(Xg, Yg, np.zeros_like(Xg), color='green', alpha=0.3)

    # Initialize panel, shadow, and diagonal line
    panel_poly = Poly3DCollection([], alpha=0.7, edgecolor='black')
    shadow_poly = Poly3DCollection([], facecolors='gray', alpha=0.5, edgecolor='black')

    # --- FIX: Dummy line to avoid crash ---
    dummy_line = np.array([[[0, 0, 0], [0, 0, 0]]])
    diagonal_line = Line3DCollection(dummy_line, colors='black', linewidths=2)

    ax.add_collection3d(panel_poly)
    ax.add_collection3d(shadow_poly)
    ax.add_collection3d(diagonal_line)

    # Initialize quivers for arrows
    panel_normal_arrow = ax.quiver(0, 0, 0, 0, 0, 0, color='blue', length=2, normalize=True)
    vertical_reference_arrow = ax.quiver(0, 0, 0, 0, 0, 1, color='gray', length=2, normalize=True)

    # Legend
    legend_elements = [
        Line2D([0], [0], color='blue', lw=2, label='Panel Normal Vector'),
        Line2D([0], [0], color='gray', lw=2, label='Zero Azimuth & Tilt (Vertical)')
    ]
    ax.legend(handles=legend_elements, loc='upper left')

    def composite_rotation(phi, alpha):
        Rz = np.array([
            [np.cos(phi), -np.sin(phi), 0],
            [np.sin(phi), np.cos(phi), 0],
            [0, 0, 1]
        ])
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(alpha), -np.sin(alpha)],
            [0, np.sin(alpha), np.cos(alpha)]
        ])
        return Rz @ Rx

    def compute_shadow(phi_p, alpha_p, S, local_corners, H):
        R = composite_rotation(phi_p, alpha_p)
        global_corners = (R @ local_corners.T).T + np.array([0, 0, H])

        if S[2] <= 0:
            return global_corners, np.full_like(global_corners, np.nan)

        panel_normal = R @ np.array([0, 0, 1])

        if np.abs(np.dot(panel_normal, S)) < 1e-6:
            shadow_corners = np.zeros((4, 3))
        else:
            shadow_corners = np.array([C - (C[2] / S[2]) * S for C in global_corners])
            shadow_corners[:, 2] = 0

        return global_corners, shadow_corners

    def update(frame):
        nonlocal panel_normal_arrow
        phi_p, alpha_p = optimal_angles[frame]
        phi_s_deg, alpha_s_deg = sun_positions[frame]

        phi_s = np.radians(phi_s_deg)
        alpha_s = np.radians(alpha_s_deg)
        S = np.array([
            np.cos(alpha_s) * np.cos(phi_s),
            np.cos(alpha_s) * np.sin(phi_s),
            np.sin(alpha_s)
        ])

        global_corners, shadow_corners = compute_shadow(phi_p, alpha_p, S, local_corners, H)

        # Front and back face (fixed color)
        front_face = [global_corners]         # Normal order
        back_face = [global_corners[::-1]]     # Reversed order

        panel_poly.set_verts(front_face + back_face)
        panel_poly.set_facecolor(['cyan', 'lightgray'])  # Always cyan front, gray back

        shadow_poly.set_verts([shadow_corners])

        # Diagonal line from corner 0 to corner 2
        diag = np.array([[global_corners[0], global_corners[2]]])
        diagonal_line.set_segments(diag)

        # Remove previous panel normal arrow
        panel_normal_arrow.remove()

        # Compute new panel normal
        R = composite_rotation(phi_p, alpha_p)
        normal_vector = R @ np.array([0, 0, 1])

        # Center of panel
        center = np.mean(global_corners, axis=0)

        # Update panel normal arrow
        panel_normal_arrow = ax.quiver(center[0], center[1], center[2],
                                       normal_vector[0], normal_vector[1], normal_vector[2],
                                       color='blue', length=2, normalize=True)

        return panel_poly, shadow_poly, panel_normal_arrow, diagonal_line

    ani = animation.FuncAnimation(fig, update, frames=len(times), interval=200, blit=False)
    plt.show()



# ------------------------------------------
# Optimization Functions
# ------------------------------------------
# Objective function for maximizing alignment
def objective(x, S):
    phi_p, alpha_p = x
    normal = np.array([
        np.sin(phi_p) * np.sin(alpha_p),
        -np.cos(phi_p) * np.sin(alpha_p),
        np.cos(alpha_p)
    ])
    return -np.dot(normal, S)

# Objective function with goal seeking,
#  target_alignment should be between 0 and 1
def objective_goal_seeking(x, S, target_alignment=1.0):
    phi_p, alpha_p = x
    normal = np.array([
        np.sin(phi_p) * np.sin(alpha_p),
        -np.cos(phi_p) * np.sin(alpha_p),
        np.cos(alpha_p)
    ])
    dot_product = np.dot(normal, S)
    return (dot_product - target_alignment)**2

def shadow_constraint(x, S, plant_bounds, local_corners, H):
    plant_bound_neg_x = plant_bounds['neg_x']
    plant_bound_pos_x = plant_bounds['pos_x']
    plant_bound_neg_y = plant_bounds['neg_y']
    plant_bound_pos_y = plant_bounds['pos_y']

    _, shadow_corners = compute_shadow(x[0], x[1], S, local_corners, H)

    if np.all(shadow_corners == 0):
        return 1.0

    penalty = 0.0
    for corner in shadow_corners:
        x, y = corner[0], corner[1]
        if x > plant_bound_pos_x:
            penalty += (x - plant_bound_pos_x)**2
        elif x < plant_bound_neg_x:
            penalty += (plant_bound_neg_x - x)**2
        if y > plant_bound_pos_y:
            penalty += (y - plant_bound_pos_y)**2
        elif y < plant_bound_neg_y:
            penalty += (plant_bound_neg_y - y)**2

    penalty = penalty

    return -penalty


def shadow_constraint_hard(x, S, plant_bounds, local_corners, H):
    _, shadow_corners = compute_shadow(x[0], x[1], S, local_corners, H)

    if np.all(shadow_corners == 0):
        return -1.0  # Heavy violation if shadow cannot be computed

    margin = 0.01  # Small safe margin

    min_x = plant_bounds['neg_x'] + margin
    max_x = plant_bounds['pos_x'] - margin
    min_y = plant_bounds['neg_y'] + margin
    max_y = plant_bounds['pos_y'] - margin

    min_violation = np.inf  # Track worst violation

    for corner in shadow_corners:
        x_c, y_c = corner[0], corner[1]
        violations = [
            x_c - min_x,     # must be >= 0
            max_x - x_c,     # must be >= 0
            y_c - min_y,     # must be >= 0
            max_y - y_c      # must be >= 0
        ]
        min_violation = min(min_violation, *violations)

    return min_violation  # Must be ≥ 0 to satisfy


def optimize_panel_angles(S, alpha_s, local_corners, MIN_SUN_ALTITUDE_DEG, H, plant_bounds, target_alignment=1.0, x0_prev=None):
    if np.degrees(alpha_s) < MIN_SUN_ALTITUDE_DEG:
        phi_p = np.arctan2(S[1], S[0])
        alpha_p = np.pi / 2  # Fully vertical panel if Sun too low
        return phi_p, alpha_p

    # x0 = [np.arctan2(S[1], S[0]), np.arccos(S[2])]  # Initial guess: face toward sun
    if x0_prev is None:
        x0 = [np.arctan2(S[1], S[0]), np.arccos(S[2])]
    else:
        x0 = x0_prev

    azimuth_bounds = (-2 * np.pi / 3, 2 * np.pi / 3)  # ±120° in radians
    tilt_bounds = (np.radians(5), np.pi / 2)     # 5° to 90° in radians

    bounds = [azimuth_bounds, tilt_bounds]

    constraints = [{'type': 'ineq', 'fun': shadow_constraint_hard, 'args': (S, plant_bounds, local_corners, H)}]

    result = minimize(
        objective_goal_seeking, x0,
        args=(S, target_alignment),
        method='SLSQP',
        options={'ftol': 1e-9, 'disp': True, 'maxiter': 50000, 'eps': 1e-11},
        bounds=bounds,
        constraints=constraints
    )

    return tuple(result.x) if result.success else (x0[0], x0[1])


def optimize_panel_angles_no_constraints(S, alpha_s, local_corners, MIN_SUN_ALTITUDE_DEG, H, plant_bounds, target_alignment=1.0):
    if np.degrees(alpha_s) < MIN_SUN_ALTITUDE_DEG:
        phi_p = np.arctan2(S[1], S[0])
        alpha_p = np.pi / 2  # Fully vertical panel if Sun too low
        return phi_p, alpha_p

    x0 = [np.arctan2(S[1], S[0]), np.arccos(S[2])]  # Initial guess: face toward sun
    azimuth_bounds = (-2 * np.pi / 3, 2 * np.pi / 3)  # ±120° in radians
    tilt_bounds = (np.radians(5), np.pi / 2)     # 5° to 60° in radians

    bounds = [azimuth_bounds, tilt_bounds]

    result = minimize(
        objective_goal_seeking, x0,
        args=(S, target_alignment),
        method='SLSQP',
        options={'ftol': 1e-9, 'disp': True},
        bounds=bounds
    )

    return tuple(result.x) if result.success else (x0[0], x0[1])



def figure_one(solpos, times, min_sun_altitude_deg=35, save_path="figure1_combined_vertical.png"):
    """
    Generates a vertically stacked figure with:
    (1a) Polar solar path (65% height).
    (1b) Elevation vs. time (35% height).
    """

    # Font config
    mpl.rcParams['font.family'] = 'serif'

    # Extract data
    azimuth_rad = np.radians(solpos['azimuth'].values)
    elevation = solpos['apparent_elevation'].values
    times_str = times.strftime('%H:%M')

    # Color gradient based on time
    norm = plt.Normalize(0, len(times_str))
    cmap = cm.viridis
    color_vals = cmap(norm(np.arange(len(times_str))))

    # === Create custom grid layout ===
    fig = plt.figure(figsize=(6.5, 9))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[0.65, 0.35], figure=fig)

    # === (1a) Polar Plot ===
    ax1 = fig.add_subplot(gs[0], projection='polar')
    ax1.set_theta_zero_location('N')
    ax1.set_theta_direction(-1)
    ax1.set_rlim(0, 90)
    ax1.set_title("Azimuth vs. Elevation", fontsize=14, pad=20)

    points1a = np.array([azimuth_rad, elevation]).T.reshape(-1, 1, 2)
    segments1a = np.concatenate([points1a[:-1], points1a[1:]], axis=1)
    lc1a = LineCollection(segments1a, colors=color_vals, linewidths=3.0)
    ax1.add_collection(lc1a)

    fig.text(0.08, 0.92, "(a)", fontsize=14, ha='left', va='top')

    # === (1b) Elevation vs. Time ===
    ax2 = fig.add_subplot(gs[1])
    x_vals = np.arange(len(times_str))
    points1b = np.array([x_vals, elevation]).T.reshape(-1, 1, 2)
    segments1b = np.concatenate([points1b[:-1], points1b[1:]], axis=1)
    lc1b = LineCollection(segments1b, colors=color_vals, linewidths=3.0)
    ax2.add_collection(lc1b)

    ax2.axhline(min_sun_altitude_deg, color='black', linestyle='--',
                label=f'Min Op. Elevation ({min_sun_altitude_deg}$^\\circ$)', linewidth=2)

    ax2.set_xlim(0, len(times_str) - 1)
    ax2.set_ylim(0, np.max(elevation) + 10)
    ax2.set_xlabel('Time', fontsize=14)
    ax2.set_ylabel('Sun Elevation ($^\circ$)', fontsize=14)
    ax2.set_xticks(x_vals[::12])
    ax2.set_xticklabels(times_str[::12], rotation=45)
    ax2.tick_params(axis='x', labelsize=11)
    ax2.tick_params(axis='y', labelsize=11)
    ax2.legend(fontsize=11, loc='lower right')
    ax2.grid(True, linestyle=':', color='gray')

    fig.text(0.08, 0.42, "(b)", fontsize=14, ha='left', va='top')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()

def figure_two(optimal_angles_with, optimal_angles_without, times, save_path="figure2_panel_angles_over_time.png"):
    """
    Generates Figure 2:
      Compares panel azimuth and tilt angles over time for constrained vs. unconstrained optimization,
      with a shared color gradient applied to the constrained plots.
    """
    # Apply serif font
    mpl.rcParams['font.family'] = 'serif'

    # Unpack and convert to degrees
    phi_with, alpha_with = zip(*optimal_angles_with)
    phi_without, alpha_without = zip(*optimal_angles_without)
    phi_with = np.degrees(phi_with)
    alpha_with = np.degrees(alpha_with)
    phi_without = np.degrees(phi_without)
    alpha_without = np.degrees(alpha_without)

    time_labels = times.strftime('%H:%M')
    x_vals = np.arange(len(times))

    # Setup color gradient
    norm = plt.Normalize(0, len(times))
    cmap = cm.viridis
    colors = cmap(norm(x_vals))

    # Create figure and subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 4), sharex=True)

    # === (2a) Azimuth ===
    phi_points = np.array([x_vals, phi_with]).T.reshape(-1, 1, 2)
    phi_segments = np.concatenate([phi_points[:-1], phi_points[1:]], axis=1)
    lc_phi = LineCollection(phi_segments, colors=colors, linewidths=3)
    ax1.add_collection(lc_phi)
    ax1.plot(time_labels, phi_without, label='Unconstrained', color='gray', linestyle='--', linewidth=3)

    ax1.set_ylabel('Azimuth (°)', fontsize=14)
    ax1.tick_params(labelsize=11)
    ax1.grid(True, linestyle=':', color='gray')

    # === (2b) Tilt ===
    alpha_points = np.array([x_vals, alpha_with]).T.reshape(-1, 1, 2)
    alpha_segments = np.concatenate([alpha_points[:-1], alpha_points[1:]], axis=1)
    lc_alpha = LineCollection(alpha_segments, colors=colors, linewidths=3)
    ax2.add_collection(lc_alpha)
    ax2.plot(time_labels, alpha_without, label='Unconstrained', color='gray', linestyle='--', linewidth=3)

    ax2.set_ylabel('Tilt (°)', fontsize=14, labelpad=22)  # moved label further right
    ax2.set_xlabel('Time', fontsize=14)
    ax2.tick_params(axis='x', rotation=45, labelsize=11)
    ax2.tick_params(axis='y', labelsize=11)
    ax2.grid(True, linestyle=':', color='gray')
    ax2.set_xticks(time_labels[::12])

    # Add shared legend using proxy artists
    constrained_proxy = Line2D([0], [0], color='forestgreen', linewidth=3, label='Pointwise Constrained')
    unconstrained_proxy = Line2D([0], [0], color='gray', linestyle='--', linewidth=3, label='Unconstrained Shadows')
    ax1.legend(handles=[constrained_proxy, unconstrained_proxy], fontsize=12, loc='upper right')
    # ax2.legend(handles=[constrained_proxy, unconstrained_proxy], fontsize=12, loc='lower left')

    # Align constrained line plots
    ax1.set_xlim(0, len(times) - 1)

    # Subfigure labels
    fig.text(0.97, 0.80, "(a)", fontsize=14, ha='left', va='center')
    fig.text(0.97, 0.40, "(b)", fontsize=14, ha='left', va='center')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()

def figure_three(alignment_history, required_radiation, save_path="figure3_radiation_vs_alignment.png"):
    """
    Generates Figure 3:
      Line plot showing total radiation vs. alignment target, with a threshold line and refinement path arrow.

    Parameters:
        alignment_history (list of tuples): [(alignment_target, total_radiation)]
        required_radiation (float): Required radiation threshold
        save_path (str): Path to save the output figure
    """
    mpl.rcParams['font.family'] = 'serif'

    alignment_targets, radiation_values = zip(*alignment_history)

    # Determine success/failure
    success_flags = [rad >= required_radiation for rad in radiation_values]

    fig, ax = plt.subplots(figsize=(6, 4))

    # Scatter points with color-coded success/failure
    for x, y, success in zip(alignment_targets, radiation_values, success_flags):
        ax.scatter(x, y, color='green' if success else 'red', s=80, zorder=3)

    # Line connecting refinement steps
    ax.plot(alignment_targets, radiation_values, color='blue', linestyle='-', linewidth=2, zorder=2)

    # Required radiation threshold line
    ax.axhline(required_radiation, color='black', linestyle='--')

    # Axis labels
    ax.set_xlabel("Alignment Target", fontsize=14)
    ax.set_ylabel("Total Radiation on the Ground ", fontsize=14)
    ax.legend(fontsize=14)
    ax.grid(True, linestyle=':', color='gray')
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)

    # Draw shorter arrow (halfway along the refinement path)
    x0, y0 = alignment_targets[0], radiation_values[0]
    x1, y1 = alignment_targets[-1], radiation_values[-1]

    # Compute midpoint halfway toward the final point
    x_half = x0 + 0.75 * (x1 - x0)
    y_half = y0 + 0.5 * (y1 - y0)
    x_q = x0 + 0.25 * (x1 - x0)
    y_q = y0 + 0.25 * (y1 - y0)
    x_lq = x0 + 0.75 * (x1 - x0)
    y_lq = y0 + 0.75 * (y1 - y0)

    ax.annotate('',
                xy=(x_lq, y_lq),
                xytext=(x_q, y_q),
                arrowprops=dict(facecolor='black', shrink=0.05, width=2, headwidth=8),
                fontsize=12, ha='center', va='bottom')
    
    # Place separate text label near the midpoint
    ax.text(x_half + 0.09, y_half + 0.03 * (max(radiation_values) - min(radiation_values)),  # slightly above arrow
            'Refinement Direction', fontsize=14, ha='center')

    ax.text(1, required_radiation + 0.01 * (max(radiation_values) - min(radiation_values)),
            'Required Radiation', fontsize=14, ha='right', va='bottom')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()


def render_shadow_frame(phi_p, alpha_p, S, local_corners, H, plant_bounds, title=None, save_path=None):
    """
    Renders a 3D plot showing panel orientation and shadow projection at a given timestamp.

    Parameters:
        phi_p, alpha_p (float): Panel azimuth and tilt angles in radians
        S (ndarray): Sun direction vector
        local_corners (ndarray): Panel corner coordinates
        H (float): Panel height
        plant_bounds (dict): Plant boundary extents
        title (str): Optional (ignored to omit it now)
        save_path (str): If provided, saves the figure to this path
    """
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from utilities import compute_shadow
    import matplotlib.ticker as ticker
    mpl.rcParams['font.family'] = 'serif'

    # Transform panel corners
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(alpha_p), -np.sin(alpha_p)],
                   [0, np.sin(alpha_p), np.cos(alpha_p)]])
    Rz = np.array([[np.cos(phi_p), -np.sin(phi_p), 0],
                   [np.sin(phi_p), np.cos(phi_p), 0],
                   [0, 0, 1]])
    R = Rz @ Rx

    panel_world = (R @ local_corners.T).T + np.array([0, 0, H])
    _, shadow_corners = compute_shadow(phi_p, alpha_p, S, local_corners, H)

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(111, projection='3d')

    # Draw panel
    panel = Poly3DCollection([panel_world], alpha=0.6, facecolor='dodgerblue', edgecolor='k')
    ax.add_collection3d(panel)

    # Draw shadow on ground
    if not np.any(np.isnan(shadow_corners)):
        shadow = Poly3DCollection([shadow_corners], alpha=0.4, facecolor='gray', edgecolor='black')
        ax.add_collection3d(shadow)

    # Plant bounds
    x_min, x_max = plant_bounds['neg_x'], plant_bounds['pos_x']
    y_min, y_max = plant_bounds['neg_y'], plant_bounds['pos_y']

    # Boundary outline
    ax.plot([x_min, x_max, x_max, x_min, x_min],
            [y_min, y_min, y_max, y_max, y_min],
            [0,     0,     0,     0,     0    ],
            color='green', linestyle='--', linewidth=2)

    # Filled plant area
    plant_bounds_corners = np.array([
        [x_min, y_min, 0],
        [x_max, y_min, 0],
        [x_max, y_max, 0],
        [x_min, y_max, 0]
    ])
    plant_bounds_poly = Poly3DCollection([plant_bounds_corners], alpha=0.3, facecolor='green')
    ax.add_collection3d(plant_bounds_poly)

    # Axes limits
    ax.set_xlim(-6, 6)
    ax.set_ylim(-10, 10)
    ax.set_zlim(0, 6)

    # Labels with larger font
    ax.set_xlabel('X', fontsize=14)
    ax.set_ylabel('Y', fontsize=14)
    ax.set_zlabel('Z', fontsize=14)

    # Integer-only tick labels
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.zaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Remove title (no timestamp shown)
    # if title:
    #     ax.set_title(title)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300)
    plt.show()


def figure_four(optimal_angles, sun_positions, times, local_corners, H, plant_bounds,alphabet):
    """
    Generates Figure 5 by rendering static shadow projections at selected times (e.g., 09:00 and 12:00).

    Parameters:
        optimal_angles (list): Optimized (phi_p, alpha_p) per timestep
        sun_positions (list): (azimuth, elevation) sun position per timestep
        times (DatetimeIndex): Corresponding times
        local_corners (ndarray): Panel corner coordinates
        H (float): Panel height
        plant_bounds (dict): System area bounds
    """
    # Select only 09:00 and 12:00 frames
    target_hours = ['09:00', '12:00']
    selected = [(i, t.strftime('%H:%M')) for i, t in enumerate(times) if t.strftime('%H:%M') in target_hours]
    indices, labels = zip(*selected)

    for idx, label in zip(indices, labels):
        phi_p, alpha_p = optimal_angles[idx]
        phi_s_deg, alpha_s_deg = sun_positions[idx]
        phi_s = np.radians(phi_s_deg)
        alpha_s = np.radians(alpha_s_deg)

        S = np.array([
            np.cos(alpha_s) * np.cos(phi_s),
            np.cos(alpha_s) * np.sin(phi_s),
            np.sin(alpha_s)
        ])
        # alphabet= 'a'    
        title = f"Time: {label}"
        save_path = f"figure4{alphabet}_{label.replace(':', '')}.png"
        render_shadow_frame(phi_p, alpha_p, S, local_corners, H, plant_bounds, title=title, save_path=save_path)

