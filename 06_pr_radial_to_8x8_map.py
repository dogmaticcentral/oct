#!/usr/bin/env python3
"""
Convert radial eye measurement data to Cartesian grid through 2D interpolation.

This script reads Excel data containing measurements in radial coordinates
(mm, deg) with four quadrants (superior, inferior, temporal, nasal) and
converts it to an 8x8 Cartesian grid using 2D interpolation.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from oct_utils.visualization import plot_results

quadrants = ['superior', 'inferior', 'temporal', 'nasal']

def read_radial_data(filename:str, sheet_name: str, max_radius: float | None = None) -> pd.DataFrame:
    """
    Read radial measurement data from Excel file.

    Parameters:
    -----------
    filename : str
        Path to Excel file containing radial data

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: mm, deg, superior, inferior, temporal, nasal
    """
    df = pd.read_excel(filename, sheet_name=sheet_name)
    if max_radius is not None:
        df = df[df.mm < max_radius]
    # some messup with reading xls (the old spreadsheet format)
    df[quadrants]= df[quadrants].round().astype('Int64')


    return df

def polar_to_cartesian(r, theta):
    """
    Convert polar coordinates to Cartesian coordinates.

    Parameters:
    -----------
    r : float or array-like
        Radial distance in mm
    theta : float or array-like
        Angle in degrees

    Returns:
    --------
    tuple
        (x, y) Cartesian coordinates in mm
    """
    theta_rad = np.radians(theta)
    x = r * np.cos(theta_rad)
    y = r * np.sin(theta_rad)
    return x, y

def quadrant_to_angles(quadrant):
    """
    Get angle range for each quadrant.

    Parameters:
    -----------
    quadrant : str
        One of 'superior', 'inferior', 'temporal', 'nasal'

    Returns:
    --------
    tuple
        (start_angle, end_angle) in degrees
    """
    quadrant_ranges = {
        'superior': (45, 135),
        'temporal': (135, 225),
        'inferior': (225, 315),
        'nasal': (315, 45)  # This wraps around 0
    }
    for quad in quadrants:
        quadrant_ranges[quad] = ( quadrant_ranges[quad][0], quadrant_ranges[quad][1])
    return quadrant_ranges[quadrant]

def create_radial_points(df, max_radius_mm=None):
    """
    Create list of points in Cartesian coordinates with their values.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with radial data
    max_radius_mm : float or None
        Maximum radius to consider in mm. If None, uses all data.

    Returns:
    --------
    tuple
        (points, values) where points is array of (x, y) coordinates
        and values is array of measurement values
    """
    points = []
    values = []

    # Filter data by radius if specified
    if max_radius_mm is not None:
        df_filtered = df[df['mm'] <= max_radius_mm].copy()
    else:
        df_filtered = df.copy()

    for _, row in df_filtered.iterrows():
        r_mm = row['mm']

        # For each quadrant
        for quadrant in quadrants:
            value = row[quadrant]
            if pd.isnull(value): continue
            if value == 0: continue
            start_angle, end_angle = quadrant_to_angles(quadrant)

            # Sample multiple angles within the quadrant for better interpolation
            if quadrant == 'nasal':
                # Handle wraparound for nasal quadrant
                angles = np.concatenate([
                    np.linspace(315, 360, 5),
                    np.linspace(0, 45, 5)
                ])
            else:
                angles = np.linspace(start_angle, end_angle, 10)

            for angle in angles:
                x, y = polar_to_cartesian(r_mm, angle)
                points.append([x, y])
                values.append(value)

    return np.array(points), np.array(values)

def plot_radial_heatmap(df, logcolors=False):
    points, values = create_radial_points(df)
    values = np.asarray(values, dtype=float)
    x = np.array([p[0] for p in points], dtype=float)
    y = np.array([p[1] for p in points], dtype=float)

    plt.figure(figsize=(10, 8))
    if logcolors:
        norm = colors.LogNorm(vmin=values.min(), vmax=values.max())
    else:
        norm = colors.Normalize(vmin=values.min(), vmax=values.max())
    sc = plt.scatter(x, y, c=values, cmap="viridis", norm=norm)
    plt.colorbar(sc, label="Value (log scale)" if logcolors else "Value")

    plt.show()

def create_cartesian_grid(cell_size_mm, grid_size=8):
    """
    Create 8x8 Cartesian grid for interpolation.

    Parameters:
    -----------
    cell_size_mm : float
        Size of each cell in millimeters
    grid_size : int
        Number of cells in each dimension (default: 8)

    Returns:
    --------
    tuple
        (xi, yi, extent) where xi and yi are meshgrids and extent defines bounds
    """
    # Create grid centered at origin
    half_size = (grid_size * cell_size_mm) / 2
    x = np.linspace(-half_size, half_size, grid_size)
    y = np.linspace(-half_size, half_size, grid_size)
    xi, yi = np.meshgrid(x, y)

    extent = [-half_size, half_size, -half_size, half_size]

    return xi, yi, extent


def interpolate_to_grid(points, values, xi, yi, max_radius_mm=None):
    """
    Interpolate scattered data to regular grid.

    Parameters:
    -----------
    points : array-like
        Array of (x, y) coordinates in mm
    values : array-like
        Values at each point
    xi, yi : array-like
        Meshgrid for interpolation
    max_radius_mm : float or None
        Maximum radius in mm. Points outside are set to 0.

    Returns:
    --------
    array
        Interpolated values on grid
    """
    # Use linear interpolation with nearest-neighbor extrapolation
    grid_values = griddata(points, values, (xi, yi),
                           method='linear', fill_value=0)

    # Set values outside the measured area to 0 if max_radius specified
    if max_radius_mm is not None:
        radius_grid = np.sqrt(xi ** 2 + yi ** 2)
        grid_values[radius_grid > max_radius_mm] = 0

    return grid_values


def interpolate(shet_name: str, cell_size_mm, cells_per_side, plot=False):
    """
    Main function to execute the radial to Cartesian conversion.
    """
    # Configuration
    input_file = 'data/curcio_ref_pr_densities.xls'  # Change to your file name
    # outname base
    base_name  = shet_name.lower().replace(' ', '_')
    max_radius = cells_per_side // 2 * cell_size_mm * 1.5

    # Read data
    print("Reading radial data...")
    df = read_radial_data(input_file, sheet_name=shet_name, max_radius=max_radius)
    if plot:
        print("Plotting radial data...")
        plot_radial_heatmap(df)

    # Create radial points
    print("Converting to Cartesian coordinates...")
    points, values = create_radial_points(df, max_radius_mm=max_radius)

    # Create Cartesian grid
    print("Creating 8x8 grid...")
    xi, yi, extent = create_cartesian_grid(cell_size_mm=cell_size_mm, grid_size=cells_per_side)

    # Interpolate
    print("Performing 2D interpolation...")
    grid_values = interpolate_to_grid(points, values, xi, yi)

    # Plot results
    if plot:
        print("Plotting results...")
        plot_results(grid_values, extent, cell_size_mm, f"figures/{base_name}_grid.png", label=shet_name)

    output_df = pd.DataFrame(grid_values)
    # Save interpolated values to CSV
    output_df.to_csv(f'data/{base_name}.csv', index=False)
    print(f"Interpolated grid saved to data/{base_name}.csv")



def main():
    plot = True
    cell_size_mm   = 0.86
    cells_per_side = 8

    for sheet_name in ["Rods per sq mm", "Cones per sq mm"]:
        interpolate(sheet_name, cell_size_mm=cell_size_mm, cells_per_side=cells_per_side, plot=plot)


if __name__ == "__main__":
    main()
