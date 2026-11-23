#! /usr/bin/env python3
import argparse
import os

import numpy as np
import pandas as pd

from oct_utils.data_structures import PosteriorPoleData
from oct_utils.progression_video import make_progression_video

# with --all, eyes with fewer time points or a shorter follow-up are skipped
MIN_TIMEPOINTS_ALL = 3
MIN_SPAN_YEARS_ALL = 3


def read_all_maps(scratch_dir: str) -> dict[tuple[str, str], dict[float, pd.DataFrame]]:
    """ Interpolated maps for every eye, keyed by (alias, laterality) and then by age;
        repeated scans at the same age are averaged."""
    maps_per_eye = {}
    for data_group in ["controls", "patients"]:
        oct_df = pd.read_excel(f"{scratch_dir}/interpolated_maps.{data_group}.xlsx")
        for index_value in oct_df.index:
            ppd = PosteriorPoleData()
            ppd.pd_dataframe_read(oct_df, index_value, fussy=False)
            if ppd.interpolated_map is None: continue
            # key on the alias as read, because the controls' aliases get reformatted on read
            maps_per_age = maps_per_eye.setdefault((ppd.alias, ppd.laterality), {})
            maps_per_age.setdefault(ppd.age_at_test, []).append(ppd.interpolated_map)
    return {eye: {age: pd.concat(maps).groupby(level=0).mean() for age, maps in sorted(maps_per_age.items())}
            for eye, maps_per_age in maps_per_eye.items()}


def read_maps(scratch_dir: str, alias: str, laterality: str) -> dict[float, pd.DataFrame]:
    """ Interpolated maps for one eye, keyed by age; repeated scans at the same age are averaged."""
    return read_all_maps(scratch_dir).get((alias, laterality), {})


def fill_gaps_in_time(maps: dict[float, pd.DataFrame]) -> dict[float, pd.DataFrame]:
    """ Very conservative filling of missing cells: a cell missing at some age is filled only by linear
        interpolation in age between the closest earlier and later scans in which the same cell was measured.
        Nothing is extrapolated (cells missing before the first or after the last measurement stay missing),
        and no values are borrowed from neighboring cells."""
    ages = np.array(list(maps.keys()), dtype=float)
    stack = np.stack([m.to_numpy(dtype=float) for m in maps.values()])  # (n_ages, rows, cols)
    filled = stack.copy()
    for row, col in np.ndindex(stack.shape[1:]):
        values = stack[:, row, col]
        valid = ~np.isnan(values)
        if valid.sum() < 2: continue
        gaps = ~valid & (ages > ages[valid][0]) & (ages < ages[valid][-1])
        filled[gaps, row, col] = np.interp(ages[gaps], ages[valid], values[valid])
    n_filled = int(np.isnan(stack).sum() - np.isnan(filled).sum())
    n_left = int(np.isnan(filled).sum())
    print(f"filled {n_filled} missing cells by interpolation in age, {n_left} left missing")
    return {age: pd.DataFrame(filled[i], index=m.index, columns=m.columns)
            for i, (age, m) in enumerate(maps.items())}


def fill_edges_in_space(maps: dict[float, pd.DataFrame]) -> dict[float, pd.DataFrame]:
    """ Conservative extrapolation to the edge of the grid: a missing cell on the border of a map is set to
        the mean of its measured direct (up/down/left/right) neighbors in the same scan, i.e. the thickness is
        held constant out to the edge rather than extrapolated with a slope. Only measured neighbors are used,
        so filled values never propagate further, and interior cells are left alone."""
    filled_maps = {}
    n_filled = n_left = 0
    for age, m in maps.items():
        values = m.to_numpy(dtype=float)
        filled = values.copy()
        n_rows, n_cols = values.shape
        for row, col in np.ndindex(values.shape):
            on_edge = row in (0, n_rows - 1) or col in (0, n_cols - 1)
            if not on_edge or not np.isnan(values[row, col]): continue
            neighbors = [values[r, c] for r, c in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
                         if 0 <= r < n_rows and 0 <= c < n_cols and not np.isnan(values[r, c])]
            if neighbors:
                filled[row, col] = np.mean(neighbors)
                n_filled += 1
        n_left += int(np.isnan(filled).sum())
        filled_maps[age] = pd.DataFrame(filled, index=m.index, columns=m.columns)
    print(f"filled {n_filled} missing edge cells from their neighbors, {n_left} left missing")
    return filled_maps


def parse_args():
    parser = argparse.ArgumentParser(description="Video of the thickness map progression for one patient's eye.")
    parser.add_argument("alias", nargs="?", help="patient/control alias, e.g. 'Alex Apple'")
    parser.add_argument("eye", nargs="?", choices=["OD", "OS"], help="laterality")
    parser.add_argument("-a", "--all", action="store_true",
                        help=f"make videos for all aliases and eyes, skipping those with an existing video, "
                             f"fewer than {MIN_TIMEPOINTS_ALL} time points, "
                             f"or a time span shorter than {MIN_SPAN_YEARS_ALL} years")
    parser.add_argument("-o", "--outdir", default="/home/ivana/scratch/abca4_oct/progression_video",
                        help="output directory (default: %(default)s)")
    parser.add_argument("-s", "--seconds", type=float, default=20,
                        help="video length in seconds (default: %(default)s)")
    parser.add_argument("-n", "--interp-points", type=int, default=400,
                        help="number of frames, evenly spaced in age over the whole age range (default: %(default)s)")
    parser.add_argument("--hold", type=float, default=3,
                        help="seconds to freeze on the last frame at the end of the video, "
                             "included in --seconds (default: %(default)s)")
    args = parser.parse_args()
    if args.all and (args.alias or args.eye):
        parser.error("give either alias and eye, or --all, not both")
    if not args.all and not (args.alias and args.eye):
        parser.error("alias and eye are required unless --all is given")
    if args.seconds <= 0 or args.interp_points < 2:
        parser.error("seconds must be positive and interp-points at least 2")
    if not 0 <= args.hold < args.seconds:
        parser.error("hold must be non-negative and shorter than seconds")
    return args


def video_name(outdir: str, alias: str, eye: str) -> str:
    return f"{outdir}/{alias.replace(' ', '_')}_{eye}_progression.mp4"


def make_eye_video(maps: dict[float, pd.DataFrame], alias: str, eye: str, args):
    # prefer the same cell's own measurements at other ages; only then fall back on the neighbors
    maps = fill_gaps_in_time(maps)
    maps = fill_edges_in_space(maps)
    make_progression_video(list(maps.keys()), [m.to_numpy(dtype=float) for m in maps.values()],
                           args.seconds, args.interp_points, video_name(args.outdir, alias, eye),
                           hold=args.hold, label=f"{alias} {eye}")


def main():
    args = parse_args()
    scratch_dir = "/home/ivana/scratch/abca4_oct/xlsx"
    os.makedirs(args.outdir, exist_ok=True)

    if not args.all:
        maps = read_maps(scratch_dir, args.alias, args.eye)
        if len(maps) < 2:
            print(f"need at least two time points for a video, found {len(maps)} for '{args.alias}' {args.eye}")
            exit(1)
        make_eye_video(maps, args.alias, args.eye, args)
        return

    for (alias, eye), maps in sorted(read_all_maps(scratch_dir).items()):
        ages = list(maps.keys())
        # if os.path.exists(video_name(args.outdir, alias, eye)):
        #     print(f"skipping '{alias}' {eye}: video already exists")
        if len(ages) < MIN_TIMEPOINTS_ALL:
            print(f"skipping '{alias}' {eye}: only {len(ages)} time point(s)")
        elif ages[-1] - ages[0] < MIN_SPAN_YEARS_ALL:
            print(f"skipping '{alias}' {eye}: time points span only {ages[-1] - ages[0]:.1f} years")
        else:
            print(f"making video for '{alias}' {eye}")
            make_eye_video(maps, alias, eye, args)


#######################
if __name__ == "__main__":
    main()
