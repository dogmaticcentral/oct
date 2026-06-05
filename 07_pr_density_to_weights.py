#!/usr/bin/env python3
"""
Combine rod and cone densities into a weight map for weighted avf retinal thickness scoring
"""
import json
from pprint import pformat, pprint

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

def create_weights_map(interpolated_df, cell_size_mm, cells_per_side, invert=False, plot=False):

    relative_contribution_rods  = 2
    relative_contribution_cones = 1
    weight_df = (relative_contribution_rods*z_normalize_df(interpolated_df["rods_per_sq_mm"])
                 + relative_contribution_cones*z_normalize_df(interpolated_df["cones_per_sq_mm"]))

    a, b = 2, 100
    weight_df_min = weight_df.min().min()
    weight_df_max = weight_df.max().max()
    # Apply min-max normalization to new range [2, 100]
    normalized_weight_df = a + (weight_df - weight_df_min) * (b - a) / (weight_df_max - weight_df_min)
    # experimental: inverted map for use in Usher's
    if invert:
        normalized_weight_df = 102 - normalized_weight_df

    outfnm = "data/physiological_weights.inverted.json" if invert else "data/physiological_weights.json"
    with open(outfnm, "w") as outf:
        optm_data = {
            "parameters": {
                "cell_size_mm": cell_size_mm,
                "cells_per_side": cells_per_side,
            },
            "inverted": False,
            "relative_contribution_rods": relative_contribution_rods,
            "relative_contribution_cones": relative_contribution_cones,
            "range": [a, b],
            "weights": np.asarray(normalized_weight_df).astype(np.int8).tolist()
        }
        pprint(optm_data, stream=outf)

    if plot:
        half_size = (cells_per_side * cell_size_mm) / 2
        extent = [-half_size, half_size, -half_size, half_size]
        # output_file = ""
        output_file = "figures/weights_grid.inverted.png" if invert else "figures/weights.png"
        plot_results(normalized_weight_df, extent, cell_size_mm,
                     output_file, colorbar_label="Cell weight",
                     title = "Averaging weights based on photoreceptor densities")


def main():
    plot = True
    cell_size_mm   = 0.86
    cells_per_side = 8
    interpolated_df = {}
    invert = True   # for Usher's
    for density_map in ["cones_per_sq_mm", "rods_per_sq_mm"]:
        interpolated_df[density_map] = pd.read_csv(f"data/{density_map}.csv")

    create_weights_map(interpolated_df, cell_size_mm, cells_per_side, invert=invert, plot=plot)


if __name__ == "__main__":
    main()
