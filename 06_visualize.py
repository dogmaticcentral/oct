#! /usr/bin/env python
import pandas as pd
from oct_utils.data_structures import PosteriorPoleData
from oct_utils.plotting import plot_thickness_map


def main():
    top_level_dir  = f"/media/ivana/portable/ush2a/oct/xml"
    patient_homedir = f"{top_level_dir}/all"
    scratch_dir = "/home/ivana/scratch/ush2a_oct"
    orig_dir = f"{scratch_dir}/original"
    intrp_dir = f"{scratch_dir}/interpolated"

    oct_df = pd.read_excel("interpolated_maps.xlsx")
    for index_value in oct_df.index:
        print(f"Index: {index_value}")
        ppd = PosteriorPoleData()
        ppd.pd_dataframe_read(oct_df, index_value, fussy=True, xml_dir_path=patient_homedir)
        plot_thickness_map(ppd, orig_dir, thck_map="original")
        plot_thickness_map(ppd, intrp_dir, thck_map="interp")

#######################
if __name__ == "__main__":
    main()
