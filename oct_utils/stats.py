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
            [43, 53, 56, 55, 55, 56, 53, 43], [35, 55, 48, 29, 29, 48, 33, 9], [30, 5, 2, 2, 2, 3, 2, 3], [25, 2, 2, 2, 2, 2, 2, 5], [25, 2, 2, 2, 2, 2, 2, 5], [30, 5, 2, 2, 2, 28, 2, 3], [35, 99, 89, 61, 61, 89, 99, 16], [56, 88, 100, 99, 99, 99, 88, 56]
            ])
    else:
        raise Exception(f"Unrecognized wighting scheme: {weight_type}")

    sum_of_weights = weights[df.notna()].sum().sum()
    wavg = (df*weights).sum().sum()/sum_of_weights
    return float(wavg) # otherwise we get tthe np.float
