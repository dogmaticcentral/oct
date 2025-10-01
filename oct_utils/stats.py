import numpy as np
import pandas as pd

from abca4_87_oct.oct_utils.data_structures import PosteriorPoleData


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
            # [3, 19, 30, 35, 35, 30, 19, 3],
            # [14, 48, 46, 49, 49, 46, 28, 8],
            # [25, 37, 22, 32, 32, 82, 31, 15],
            # [30, 29, 27, 77, 84, 45, 34, 20],
            # [30, 29, 27, 61, 97, 45, 34, 20],
            # [25, 37, 2, 44, 44, 100, 31, 15],
            # [15, 80, 77, 71, 71, 77, 67, 12],
            # [9, 41, 59, 66, 66, 59, 41, 9]

             [15, 19, 20, 19, 19, 20, 19, 7],
             [18, 19, 17, 11, 11, 17, 11, 2],
             [11, 3, 6, 22, 22, 9, 2, 3],
             [9, 5, 33, 95, 92, 39, 6, 3],
             [10, 5, 33, 100, 68, 39, 6, 3],
             [11, 3, 11, 18, 18, 3, 2, 9],
             [13, 10, 24, 21, 21, 30, 23, 26],
             [13, 14, 33, 33, 33, 33, 30, 19]

        ])
    else:
        raise Exception(f"Unrecognized wighting scheme: {weight_type}")

    sum_of_weights = weights[df.notna()].sum().sum()
    wavg = (df*weights).sum().sum()/sum_of_weights
    return float(wavg) # otherwise we get tthe np.float
