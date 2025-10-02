import numpy as np
from matplotlib import pyplot as plt


def plot_results(grid_values, extent, cell_size_mm, output_file='', label='Measurement Value'):
    """
    Plot the interpolated grid.

    Parameters:
    -----------
    grid_values : array
        Interpolated values on grid
    extent : list
        Extent of the grid [xmin, xmax, ymin, ymax]
    cell_size_mm : float
        Size of each cell in mm
    output_file : str
        Filename for saving the plot
    """
    plt.figure(figsize=(10, 8))

    # Plot heatmap
    im = plt.imshow(grid_values, extent=extent, origin='lower',
                    cmap='viridis', aspect='equal')
    plt.colorbar(im, label=label)

    # Add grid lines
    grid_ticks = np.arange(extent[0], extent[1] + cell_size_mm, cell_size_mm)
    plt.xticks(grid_ticks)
    plt.yticks(grid_ticks)
    plt.grid(True, alpha=0.3)

    # Labels
    plt.xlabel('X (mm)')
    plt.ylabel('Y (mm)')
    plt.title(f'8x8 Grid Interpolation ({cell_size_mm:.2f} × {cell_size_mm:.2f} mm cells)')

    # Add radial reference circles at 1mm intervals
    max_radius = np.sqrt(2) * extent[1]  # Maximum visible radius
    for radius_mm in np.arange(1, max_radius, 1):
        circle = plt.Circle((0, 0), radius_mm, fill=False,
                            linestyle='--', color='gray', alpha=0.5)
        plt.gca().add_patch(circle)
        # Add radius label
        plt.text(0, radius_mm, f'{radius_mm:.0f}mm',
                 ha='center', va='bottom', fontsize=8, alpha=0.7)

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    else:
        plt.show()
