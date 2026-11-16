#! /usr/bin/env python
import argparse
import os

import pandas as pd

from oct_utils.data_structures import PosteriorPoleData
from oct_utils.plotting import plot_thickness_map, plot_rate_of_change_map, plot_progression_svg, \
    thickness_map_outname


def read_ppds_for_alias(scratch_dir: str, alias: str) -> list[PosteriorPoleData]:
    ppds = []
    for data_group in ["controls", "patients"]:
        oct_df = pd.read_excel(f"{scratch_dir}/interpolated_maps.{data_group}.xlsx")
        for index_value in oct_df.index:
            ppd = PosteriorPoleData()
            ppd.pd_dataframe_read(oct_df, index_value, fussy=False)
            # compare after reading, because the controls' aliases get reformatted on read
            if ppd.alias != alias: continue
            if ppd.interpolated_map is None: continue
            ppds.append(ppd)
    return ppds


def average_over_eyes(ppds: list[PosteriorPoleData]) -> dict[float, pd.DataFrame]:
    """ For each age, average the interpolated maps over OD and OS.
        NaNs are skipped, so if a tile (or the whole eye) is missing, the existing value is used as is."""
    maps_per_age = {}
    for ppd in ppds:
        maps_per_age.setdefault(ppd.age_at_test, []).append(ppd.interpolated_map)
    return {age: pd.concat(maps).groupby(level=0).mean() for age, maps in sorted(maps_per_age.items())}


def rates_of_change(avg_maps: dict[float, pd.DataFrame]) -> list[tuple[float, float, pd.DataFrame]]:
    ages = list(avg_maps.keys())
    rates = []
    for age_from, age_to in zip(ages[:-1], ages[1:]):
        rates.append((age_from, age_to, (avg_maps[age_to] - avg_maps[age_from]) / (age_to - age_from)))
    return rates


def plot_if_missing(ppd: PosteriorPoleData, outdir: str):
    if os.path.exists(f"{outdir}/{thickness_map_outname(ppd, 'interp')}"):
        print(f"skipping {outdir}/{thickness_map_outname(ppd, 'interp')} - exists")
        return
    plot_thickness_map(ppd, outdir, thck_map="interp")


def main():
    parser = argparse.ArgumentParser(description="Plot interpolated thickness maps and their rate of change.")
    parser.add_argument("alias", help="patient/control alias, e.g. 'Alex Apple'")
    parser.add_argument("outdir", help="output directory")
    parser.add_argument("--format", choices=["png", "svg"], default="png",
                        help="png: individual map files (default); svg: one combined document per OU/OD/OS")
    args = parser.parse_args()

    scratch_dir = "/home/ivana/scratch/abca4_oct/xlsx"

    ppds = read_ppds_for_alias(scratch_dir, args.alias)
    if not ppds:
        print(f"no interpolated maps found for '{args.alias}'")
        exit(1)

    # maps for the eye average (OU) and for each eye individually
    # (average_over_eyes on a single eye only merges repeated scans at the same age)
    maps = {"OU": average_over_eyes(ppds)}
    for laterality in sorted({ppd.laterality for ppd in ppds}):
        maps[laterality] = average_over_eyes([ppd for ppd in ppds if ppd.laterality == laterality])
    rates = {laterality: rates_of_change(lat_maps) for laterality, lat_maps in maps.items()}

    all_rate_maps = [rate.values for lat_rates in rates.values() for _, _, rate in lat_rates]
    if not all_rate_maps:
        print(f"only one time point for '{args.alias}' - no rate of change maps")

    if args.format == "svg":
        os.makedirs(args.outdir, exist_ok=True)
        for laterality in maps:
            plot_progression_svg(args.alias, laterality, maps[laterality], rates[laterality], args.outdir)
        return

    intrp_dir = f"{args.outdir}/interpolated"
    avg_dir   = f"{args.outdir}/eye_avg"
    rate_dir  = f"{args.outdir}/rate_of_change"
    for d in [intrp_dir, avg_dir, rate_dir]:
        os.makedirs(d, exist_ok=True)

    for ppd in ppds:
        plot_if_missing(ppd, intrp_dir)

    for age, avg_map in maps["OU"].items():
        avg_ppd = PosteriorPoleData(alias=args.alias, laterality="OU", age_at_test=age)
        avg_ppd.interpolated_map = avg_map
        plot_if_missing(avg_ppd, avg_dir)

    for laterality, lat_rates in rates.items():
        for age_from, age_to, rate in lat_rates:
            plot_rate_of_change_map(args.alias, laterality, age_from, age_to, rate, rate_dir)


#######################
if __name__ == "__main__":
    main()
