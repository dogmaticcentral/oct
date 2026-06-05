import numpy as np
import pandas as pd

from oct_utils.data_structures import PosteriorPoleData


def weighted_avg(ppd: PosteriorPoleData, interp=False, weight_type="") -> float:

    if interp:
        df = ppd.interpolated_map
        weights = pd.DataFrame(np.full((8, 8), 100, dtype=float))
    else:
        df = ppd.pp_map
        weights = ppd.weights

    if weight_type == "8x8":
        pass  # that's the default
    elif weight_type == "4x4":
        # the numbers here came about as follows - the xml file from spectralis
        # claims that in the 8x8 grid the dims of ecah are 0.86 x 0.86 mm
        # while the outer diameter is 3.45 mm in the bullseye grid
        # 3.45/0.86 = 4.01, thus the inner 4x4 covers it with a bit of extra on the sides
        df = df.iloc[2:6, 2:6]
        weights = weights.iloc[2:6, 2:6]

    elif weight_type == "2x2":
        df = df.iloc[3:5, 3:5]
        weights = weights.iloc[3:5, 3:5]

    elif weight_type == "concentric":
        # downweight the outer rings
        # for s, w in [(0, 5), (1, 10), (2, 50), (3, 100)]:
        for s, w in [(0, 5), (1, 25), (2, 50), (3, 100)]:
            weights.iloc[s:8-s, s:8-s] = w

    elif weight_type == "optimized":
        weights = pd.DataFrame([
            [5.0, 20.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            [5.0, 70.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            [10.0, 65.0, 5.0, 5.0, 15.0, 5.0, 5.0, 5.0],
            [90.0, 10.0, 5.0, 155.0, 250.0, 5.0, 5.0, 5.0],
            [5.0, 5.0, 5.0, 65.0, 80.0, 5.0, 5.0, 5.0],
            [5.0, 45.0, 5.0, 5.0, 5.0, 25.0, 5.0, 5.0],
            [5.0, 70.0, 80.0, 15.0, 5.0, 5.0, 5.0, 5.0],
            [5.0, 5.0, 5.0, 45.0, 130.0, 130.0, 85.0, 110.0]
        ])
    elif weight_type == "physiological":
        weights = pd.DataFrame([
            [27, 34, 36, 35, 35, 36, 34, 27],
            [22, 35, 30, 19, 19, 30, 21, 6],
            [19, 4, 12, 22, 22, 17, 2, 2],
            [16, 5, 34, 90, 91, 40, 7, 4],
            [16, 5, 34, 70, 100, 40, 7, 4],
            [19, 4, 3, 18, 18, 32, 2, 2],
            [22, 62, 56, 39, 39, 56, 62, 10],
            [35, 55, 62, 62, 62, 62, 55, 35]
        ])
    elif weight_type == "inverted":
        weights = pd.DataFrame([
            [74, 67, 65, 66, 66, 65, 67, 74],
            [79, 66, 71, 82, 82, 71, 80, 95],
            [82, 97, 89, 79, 79, 84, 100, 99],
            [85, 96, 67, 11, 10, 61, 94, 97],
            [85, 96, 67, 31, 2, 61, 94, 97],
            [82, 97, 98, 83, 83, 69, 100, 99],
            [79, 39, 45, 62, 62, 45, 39, 91],
            [66, 46, 39, 39, 39, 39, 46, 66]
       ])
    else:
        raise Exception(f"Unrecognized wighting scheme: {weight_type}")

    sum_of_weights = weights[df.notna()].sum().sum()
    wavg = (df*weights).sum().sum()/sum_of_weights
    return float(wavg) # otherwise we get tthe np.float
