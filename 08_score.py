#! /usr/bin/env python
import os

import pandas as pd
import matplotlib.pyplot as plt
from oct_utils.data_structures import PosteriorPoleData
from oct_utils.stats import weighted_avg

def plot(df_dict, x_column: str, y_column_1: str, y_column_2: str, outfnm: str) :
    fig, axes = plt.subplots(nrows=1, ncols=2, sharey=True, figsize=(10, 5))

    # Scatter plot y_column_1 vs x_column in first panel
    axes[0].scatter(df_dict["controls"][x_column], df_dict["controls"][y_column_1], label="controls")
    axes[0].scatter(df_dict["patients"][x_column], df_dict["patients"][y_column_1], color="red", label="patients")
    axes[0].set_xlabel(x_column)
    axes[0].set_ylabel(y_column_1)
    axes[0].set_ylim([210, 350])
    axes[0].legend()

    # Scatter plot y_column_2 vs x_column in second panel
    axes[1].scatter(df_dict["controls"][x_column], df_dict["controls"][y_column_2], label="controls")
    axes[1].scatter(df_dict["patients"][x_column], df_dict["patients"][y_column_2], color="red", label="patients")
    axes[1].set_xlabel(x_column)
    axes[1].set_ylabel(y_column_2)
    axes[1].legend()

    plt.savefig(outfnm)
    print(f"plot written to {outfnm}")

def main():
    top_level_dir = f"/media/ivana/portable/ush2a/oct/xml"
    scratch_dir   = "/home/ivana/scratch/ush2a_oct"
    output_columns = ['alias', 'eye', 'age_acquired', 'avg_thickness', 'wtd_avg_thickness', 'file_name', 'file_md5']

    output_df = {}
    for data_group in ["controls", "patients"]:
        output_df[data_group] = pd.DataFrame(columns=output_columns)
        oct_df = pd.read_excel(f"{scratch_dir}/interpolated_maps.{data_group}.xlsx")
        data_dir = f"{top_level_dir}/{data_group}"
        for index_value in oct_df.index:
            print(f"Index: {index_value}")
            ppd = PosteriorPoleData()
            ppd.pd_dataframe_read(oct_df, index_value, fussy=True, xml_dir_path=data_dir)
            ppd.avg_thickness = round(weighted_avg(ppd, interp=True, weight_type="8x8")*1000)
            ppd.wtd_avg_thickness = round(weighted_avg(ppd, interp=True, weight_type="physiological")*1000)
            ppd.pd_df_store_minimal(output_df[data_group])
        output_df[data_group].to_excel(f"{scratch_dir}/avg_retinal_thickness.{data_group}.xlsx")

    plot(output_df, "age_acquired", "avg_thickness", "wtd_avg_thickness", f"{scratch_dir}/avg_thckns.png")

#######################
if __name__ == "__main__":
    main()
