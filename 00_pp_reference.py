#! /usr/bin/env python3

import argparse
from statistics import mean

from oct_utils.data_structures import PosteriorPoleData
from oct_utils.plotting import plot_thickness_map
from oct_utils.progression_video import make_progression_video


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def ref_pp_map(filename: str, segment, age_group, percentile: int|str = "avg") -> PosteriorPoleData:
    # note that this parser is crude and not really guaranteed to work for
    # any layer except retina

    column = None
    if isinstance(percentile, int):
        percentile2column = {1: 1, 5: 2, 95: 3}
        column = percentile2column.get(percentile)
        if column is None:
            print(f"Percentile {percentile} not available")
            exit(1)
    ppd = PosteriorPoleData()

    # note that the data we are filling here are semi-sensible
    ppd.laterality = "OD"  # actually could be either
    ppd.alias = "Caucasian Reference"
    ppd.age_at_test = int(age_group.split("-")[0])

    inf = open(filename)
    reading = False
    cells = []
    for line in inf:
        if line[:len(segment)] == segment:
            reading = True
            continue
        if len(line.strip()) == 0:
            reading = False
            continue
        if not reading:
            continue
        tokens = line.strip().split()
        if is_float(tokens[0]):
            # this is a cheat, because 2.3 doee not really represent a float
            # but row 2 col 3
            cells = [(int(token[0]) - 1, int(token[-1]) - 1) for token in tokens]
        if line[:len(age_group)] == age_group:
            if column:
                thicknesses = [float(tokens[i])/1000 for i in range(column, 13, 3)]
            else:
                # guessing that the average is somewhere between the  5th and th 95th percentile
                thicknesses = [(float(tokens[i]) + float(tokens[i+1]))/2/1000 for i in range(2, 13, 3)]
            for i, (row, col) in enumerate(cells):
                # print(row, col, thicknesses[i])
                ppd.pp_map.loc[row, col] = thicknesses[i]
    inf.close()
    return ppd


def parse_args():
    parser = argparse.ArgumentParser(description="Reference posterior pole thickness maps, by age group.")
    parser.add_argument("--video", action="store_true",
                        help="also produce an mp4 illustrating the change in thickness with age")
    parser.add_argument("-s", "--seconds", type=float, default=20,
                        help="video length in seconds (default: %(default)s)")
    parser.add_argument("-n", "--interp-points", type=int, default=400,
                        help="number of frames, evenly spaced in age over the whole age range (default: %(default)s)")
    parser.add_argument("--hold", type=float, default=3,
                        help="seconds to freeze on the last frame at the end of the video, "
                             "included in --seconds (default: %(default)s)")
    args = parser.parse_args()
    if args.seconds <= 0 or args.interp_points < 2:
        parser.error("seconds must be positive and interp-points at least 2")
    if not 0 <= args.hold < args.seconds:
        parser.error("hold must be non-negative and shorter than seconds")
    return args


def main():

    args = parse_args()
    scratch = "/home/ivana/scratch/abca4_oct/ref_from_literature"
    ref_values_file = "data/ref_thicknesses.txt"

    age_at_test = []
    maps = []
    wavg = []
    for age_group in ["18-29", "30-39", "40-49", "50-59", "60-69"]:
        ppd = ref_pp_map(ref_values_file, "RETINA", age_group, percentile="avg")
        if ppd is None: continue
        plot_thickness_map(ppd, scratch)
        # wavg.append(weighted_avg(ppd))
        age_at_test.append(mean([int(i) for i in age_group.split("-")]))
        maps.append(ppd.pp_map.to_numpy(dtype=float))
    # plot_avg_thickness_vs_time(age_at_test, wavg, yrange=[0.25, 0.35])

    if args.video:
        if len(age_at_test) < 2:
            print("need at least two age groups for a video")
            exit(1)
        make_progression_video(age_at_test, maps, args.seconds, args.interp_points,
                               f"{scratch}/Caucasian_Reference_progression.mp4", hold=args.hold)

#######################################
if __name__ == "__main__":
    main()
