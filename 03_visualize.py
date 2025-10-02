#! /usr/bin/env python
import os

import pandas as pd

from oct_utils.data_structures import PosteriorPoleData
from oct_utils.plotting import plot_thickness_map


def main():
    top_level_dir = f"/media/ivana/portable/ush2a/oct/xml"
    scratch_dir   = "/home/ivana/scratch/ush2a_oct"

    for data_group in ["controls", "patients"]:
        oct_df = pd.read_excel(f"{scratch_dir}/interpolated_maps.{data_group}.xlsx")
        orig_dir = f"{scratch_dir}/pp_visualization/{data_group}/original"
        intrp_dir = f"{scratch_dir}/pp_visualization/{data_group}/interpolated"
        os.makedirs(orig_dir, exist_ok=True)
        os.makedirs(intrp_dir, exist_ok=True)
        data_dir = f"{top_level_dir}/{data_group}"
        for index_value in oct_df.index:
            print(f"Index: {index_value}")
            ppd = PosteriorPoleData()
            ppd.pd_dataframe_read(oct_df, index_value, fussy=True, xml_dir_path=data_dir)
            plot_thickness_map(ppd, orig_dir, thck_map="original")
            plot_thickness_map(ppd, intrp_dir, thck_map="interp")

#######################
if __name__ == "__main__":
    main()
