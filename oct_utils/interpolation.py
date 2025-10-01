from itertools import product

import numpy as np
import pandas as pd
from scipy.interpolate import LinearNDInterpolator

from oct_utils.data_structures import PosteriorPoleData


def interpolate_3d(ppds: list[PosteriorPoleData]):
    """ Function to perform 3D interpolation on a series of DataFrames """

    # defend ourselves from useless input:
    if len(ppds) == 0:
        return

    if len(ppds) == 1:
        ppds[0].interpolated_map = ppds[0].pp_map
        return

    # Convert list of DataFrames to a 3D numpy array
    data = np.array([ppd.pp_map.values for ppd in ppds])
    timepoints = np.array([ppd.age_at_test for ppd in ppds])

    # Get indices of non-NaN values
    valid_points = np.array(np.nonzero(~np.isnan(data))).T  # Get coordinates of non-NaN points
    if len(valid_points) == 0:
        print("warning: no valid points for interpolate_3d")
        ppds[0].interpolated_map = ppds[0].pp_map
        return

    # replace the indices with the non-equidistant time points
    valid_points[:, 0] = timepoints[valid_points[:, 0]]
    valid_values = data[~np.isnan(data)]  # Get corresponding values
    if len(valid_values) == 0:
        print("Warning: no valid values for interpolate_3d")
        ppds[0].interpolated_map = ppds[0].pp_map
        return

    # Use the valid points and their corresponding values to create the interpolator.
    try:
        interpolator = LinearNDInterpolator(valid_points, valid_values)
    except Exception as e:
        print(f"Warning: interpolation failed: {e}")
        for i in range(len(ppds)):
            ppds[i].interpolated_map = ppds[i].pp_map
        return

    # Generate a Grid for Interpolation:
    number_of_timepoints, width, height = data.shape
    grid_points = np.array(list(product(timepoints, range(width), range(height))))

    interpolated_values = interpolator(grid_points)

    # Reshape back to the original data shape
    interpolated_data = interpolated_values.reshape(data.shape)

    # Replace NaNs in original data with interpolated values
    filled_data = np.where(np.isnan(data), interpolated_data, data)

    for i in range(filled_data.shape[0]):
        ppds[i].interpolated_map = pd.DataFrame(filled_data[i])
