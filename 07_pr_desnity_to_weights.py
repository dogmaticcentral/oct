#!/usr/bin/env python3
"""
Combine rod and cone densities into a weight map for weighted avf retinal thickness scoring
"""
import json

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors

from oct_utils.visualization import plot_results

quadrants = ['superior', 'inferior', 'temporal', 'nasal']

def z_normalize_df(df):
    mean_all = df.values.flatten().mean()
    std_all = df.values.flatten().std()
    df_normalized = (df - mean_all) / std_all
    df_normalized[df_normalized < 0] = 0
    return df_normalized

def create_weights_map(interpolated_df, cell_size_mm, cells_per_side, plot=False):

    relative_contribution_rods  = 1
    relative_contribution_cones = 0
    weight_df = (relative_contribution_rods*z_normalize_df(interpolated_df["rods_per_sq_mm"])
                 + relative_contribution_cones*z_normalize_df(interpolated_df["cones_per_sq_mm"]))

    a, b = 2, 100
    weight_df_min = weight_df.min().min()
    weight_df_max = weight_df.max().max()
    # Apply min-max normalization to new range [2, 100]
    normalized_weight_df = a + (weight_df - weight_df_min) * (b - a) / (weight_df_max - weight_df_min)

    with open("data/physiological_weights.json", "w") as outf:
        optm_data = {
            "parameters": {
                "cell_size_mm": cell_size_mm,
                "cells_per_side": cells_per_side,
            },
            "relative_contribution_rods": relative_contribution_rods,
            "relative_contribution_cones": relative_contribution_cones,
            "range": [a, b],
            "weights": np.asarray(normalized_weight_df).astype(np.int8).tolist()
        }
        json.dump(optm_data, outf)

    if plot:
        half_size = (cells_per_side * cell_size_mm) / 2
        extent = [-half_size, half_size, -half_size, half_size]
        output_file = ""
        # output_file = "figures/weights_grid.png"
        plot_results(normalized_weight_df, extent, cell_size_mm, output_file)


def main():
    plot = True
    cell_size_mm   = 0.86
    cells_per_side = 8
    interpolated_df = {}
    for density_map in ["cones_per_sq_mm", "rods_per_sq_mm"]:
        interpolated_df[density_map] = pd.read_csv(f"data/{density_map}.csv")

    create_weights_map(interpolated_df, cell_size_mm, cells_per_side, plot=plot)


if __name__ == "__main__":
    main()
