#! /usr/bin/env python
import hashlib
import os

import pandas as pd

from oct_utils.choroid import choroid_thickness_normal
from oct_utils.data_structures import PosteriorPoleData
from oct_utils.interpolation import interpolate_3d
from oct_utils.xml_parsing import extract_pp_map


def clean_interp_values(interpolated_values):
    aliases_to_remove = []
    for alias, patient_interp_vals in interpolated_values.items():
         if not patient_interp_vals.keys():
            aliases_to_remove.append(alias)

    for alias in aliases_to_remove:
        del interpolated_values[alias]


def interpolate_single_person(homedir, alias, chorthck_df: pd.DataFrame | None = None) -> {}:

    interpolated_ppds = {}

    for eye in ["OD", "OS"]:
        eyedir = f"{homedir}/{alias}/{eye}"

        pp_data = []
        for xmlfile in [f for f in os.listdir(eyedir) if f[-4:] == ".xml"]:
            ppd = extract_pp_map(f"{eyedir}/{xmlfile}")
            if ppd is None: continue
            ppd.filename = xmlfile
            ppd.filename_md5 =  hashlib.md5(open(f"{eyedir}/{xmlfile}",'rb').read()).hexdigest()
            ppd.choroid_ok = chorthck_df is None or choroid_thickness_normal(chorthck_df, alias, ppd.age_at_test, eye)
            pp_data.append(ppd)

        # sorted_ppds = sorted([pp for pp in pp_data if pp.choroid_ok], key=lambda ppd: ppd.age_at_test)
        sorted_ppds = sorted([pp for pp in pp_data], key=lambda ppd: ppd.age_at_test)
        interpolate_3d(sorted_ppds)
        interpolated_ppds[eye] = pp_data

    return interpolated_ppds


def xml_files_to_interpolated_ppds(homedir: str,  chorthck_df: pd.DataFrame | None = None) -> (dict, dict):

    aliases_w_post_pole = sorted(os.listdir(homedir))

    interpolated_ppds = {}
    for index, alias in enumerate(aliases_w_post_pole):
        interp_ppds =  interpolate_single_person(homedir, alias, chorthck_df)
        if not interp_ppds: continue # for example, we eliminated cases with excessive choroid thickness
        interpolated_ppds[alias] = interp_ppds

    return interpolated_ppds


def interpolate_dir_to_df(data_dir) -> pd.DataFrame:

    interp_vals = xml_files_to_interpolated_ppds(data_dir, None)
    clean_interp_values(interp_vals)

    output_df = pd.DataFrame(columns=['alias', 'eye', 'age_acquired', 'file_name', 'file_md5', 'total_volume',
                                      'choroid_ok', 'pp_map', 'interpolated_map'])
    for alias, eye_dict in interp_vals.items():
        for eye, ppds in eye_dict.items():
            for ppd in ppds:
                ppd: PosteriorPoleData
                dir_path = f"{data_dir}/{alias}/{eye}"
                ppd.pd_dataframe_store(output_df, fussy= True, xml_dir_path=dir_path)
    return output_df


def main():
    top_level_dir  = f"/media/ivana/portable/ush2a/oct/xml"
    scratch_dir = "/home/ivana/scratch/ush2a_oct"

    for data_group in ["patients", "controls"]:
        data_dir = f"{top_level_dir}/{data_group}"
        output_df = interpolate_dir_to_df(data_dir)
        output_df.to_excel(f"{scratch_dir}/interpolated_maps.{data_group}.xlsx")




#######################
if __name__ == "__main__":
    main()
