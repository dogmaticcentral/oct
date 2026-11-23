

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, TwoSlopeNorm

from oct_utils.data_structures import PosteriorPoleData


def draw_missing_checkerboard(ax, shape: tuple[int, int], checks_per_tile: int = 4):
    """ Fine checkerboard covering the whole map, to be drawn before (i.e. under) the map itself:
        the colormaps leave missing (NaN) tiles transparent, so the checkerboard shows through only there."""
    n_rows, n_cols = shape[:2]
    yy, xx = np.indices((n_rows * checks_per_tile, n_cols * checks_per_tile))
    ax.imshow((yy + xx) % 2, origin="lower", cmap=ListedColormap(["white", "lightgray"]), interpolation="none",
              extent=(-0.5, n_cols - 0.5, -0.5, n_rows - 0.5))


def _rate_cmap() -> LinearSegmentedColormap:
    # reversed viridis with a white stop in the middle: the most negative rate is yellow,
    # no change is white, the most positive rate is blue
    viridis = plt.get_cmap("viridis")
    stops = [(0.0, viridis(1.0)), (0.25, viridis(0.75)), (0.5, "white"), (0.75, viridis(0.3)), (1.0, viridis(0.0))]
    cmap = LinearSegmentedColormap.from_list("viridis_r_white0", stops)
    # missing tiles are transparent, so the checkerboard underneath shows through
    # (otherwise they would show as white, i.e. as "no change")
    cmap.set_bad((0, 0, 0, 0))
    return cmap


RATE_LIMIT = 0.04  # mm/year; rates beyond +/- this saturate to the end colors of the rate colormap


def _rate_norm() -> TwoSlopeNorm:
    """ Fixed, symmetric color scale for the rate maps, with the white stop pinned to 0."""
    return TwoSlopeNorm(vcenter=0.0, vmin=-RATE_LIMIT, vmax=RATE_LIMIT)


def thickness_map_outname(ppd: PosteriorPoleData, thck_map: str="original") -> str:
    outname  = f"{ppd.alias.replace(' ', '_')}_{ppd.laterality}_"
    outname += f"{str(ppd.age_at_test).replace('.', '_')}.{thck_map}.png"
    return outname


def plot_thickness_map(ppd: PosteriorPoleData, scratch_dir: str, thck_map: str="original"):
    plt.figure()
    plt.title(f"{ppd.alias}, {ppd.age_at_test} {ppd.laterality} ({thck_map})")
    df = ppd.pp_map if thck_map == "original" else ppd.interpolated_map
    draw_missing_checkerboard(plt.gca(), np.shape(df))
    plt.imshow(df, origin="lower", cmap='YlOrRd_r', interpolation='none', vmin=0.12, vmax=0.38)
    plt.xticks([])
    plt.yticks([])
    ax = plt.gca()
    # orientation labels, aligned with the ends of each axis
    ax.text(0, -0.02, "Temporal", transform=ax.transAxes, ha="left", va="top")
    ax.text(1, -0.02, "Nasal", transform=ax.transAxes, ha="right", va="top")
    ax.text(-0.02, 0, "Inferior", transform=ax.transAxes, ha="right", va="bottom", rotation=90)
    ax.text(-0.02, 1, "Superior", transform=ax.transAxes, ha="right", va="top", rotation=90)
    plt.colorbar(label="Avg thickness (mm)")  # Show color scale
    outname = thickness_map_outname(ppd, thck_map)
    plt.savefig(f"{scratch_dir}/{outname}")
    plt.close()
    print(f"wrote {scratch_dir}/{outname}")


def plot_avg_thickness_vs_time(age_at_test, wavg, wavg_interp=None, wavg_interp_inner=None,
                               total_volume=None, xrange: list[float] | None = None, yrange: list[float] | None = None,
                               title: str | None = None, out_name: str | None = None):
    fig, ax = plt.subplots()
    if title is not None:
        ax.set_title(title)
    ax.scatter(age_at_test, wavg)
    ax.plot(age_at_test, wavg, label="weighted avg")
    if xrange is not None: ax.set_xlim(xrange)
    if yrange is not None: ax.set_ylim(yrange)

    if wavg_interp:
        ax.scatter(age_at_test, wavg_interp)
        ax.plot(age_at_test, wavg_interp, linewidth=3, label="avg, interpolated")
    if wavg_interp_inner:
        ax.scatter(age_at_test, wavg_interp_inner, color="pink")
        ax.plot(age_at_test, wavg_interp_inner, linewidth=3, label="avg, interpolated, inner", color="pink")

    ax.set_xlabel("Age at Test (years)", fontsize=16)
    ax.set_ylabel("Average Posterior Pole Thickness (mm)", fontsize=16)
    ax.legend(loc="lower center", prop={'size': 12})

    if total_volume:
        # using twinx to generate the RHS y axis and plotting according to that scale
        ax2 = ax.twinx()
        ax2.scatter(age_at_test, total_volume, color="g")
        ax2.plot(age_at_test, total_volume, color="g", label="macular volume")
        ax2.set_ylabel("Macular Volume by Spectralis (mm3)", fontsize=16)
        ax2.legend(prop={'size': 12})
    if out_name is None:
        plt.show()
    else:
        plt.savefig(out_name)


def plot_rate_of_change_map(alias: str, laterality: str, age_from: float, age_to: float, rate_map: pd.DataFrame,
                            outdir: str):
    plt.figure()
    plt.title(f"{alias}, {laterality}, {age_from} → {age_to} (rate of change)")
    plt.xticks(np.arange(8), np.arange(1, 9))
    plt.yticks(np.arange(8), np.arange(1, 9))
    draw_missing_checkerboard(plt.gca(), np.shape(rate_map))
    plt.imshow(rate_map, origin="lower", cmap=_rate_cmap(), interpolation='none', norm=_rate_norm())
    plt.xlabel("Temporal-Nasal")
    plt.ylabel("Inferior-Superior")
    plt.colorbar(label="Thickness change rate (mm/year)", extend="both")
    outname  = f"{alias.replace(' ', '_')}_{laterality}_"
    outname += f"{str(age_from).replace('.', '_')}_to_{str(age_to).replace('.', '_')}.rate.png"
    plt.savefig(f"{outdir}/{outname}")
    plt.close()
    print(f"wrote {outdir}/{outname}")


def plot_progression_svg(alias: str, laterality: str, maps: dict[float, pd.DataFrame],
                         rates: list[tuple[float, float, pd.DataFrame]], outdir: str):
    """ Interpolated maps side by side in the top row; rate of change maps in the bottom row,
        shifted right by half a map width, so that each rate map sits between the two maps it was computed from."""
    n_maps = len(maps)
    n_rows = 2 if rates else 1
    fig = plt.figure(figsize=(2.6 * n_maps + 0.8, 3.2 * n_rows + 1.5), layout="constrained")
    fig.suptitle(f"{alias}, {laterality}")
    # each map spans two grid columns, so a one-column offset is a half-width stagger
    gs = fig.add_gridspec(n_rows, 2 * n_maps)

    def setup_axes(ax, title: str, left: bool):
        ax.set_title(title, fontsize=10)
        ax.set_xticks(np.arange(8), np.arange(1, 9), fontsize=7)
        ax.set_yticks(np.arange(8), np.arange(1, 9), fontsize=7)
        ax.set_xlabel("Temporal-Nasal", fontsize=8)
        if left: ax.set_ylabel("Inferior-Superior", fontsize=8)

    map_axes = []
    for i, (age, thck_map) in enumerate(maps.items()):
        ax = fig.add_subplot(gs[0, 2 * i: 2 * i + 2])
        draw_missing_checkerboard(ax, np.shape(thck_map))
        im_map = ax.imshow(thck_map, origin="lower", cmap='RdYlBu', interpolation='none', vmin=0.12, vmax=0.38)
        setup_axes(ax, f"{age}", left=(i == 0))
        map_axes.append(ax)
    fig.colorbar(im_map, ax=map_axes, location="top", shrink=min(1.0, 3 / n_maps), label="Avg thickness (mm)")

    if rates:
        rate_axes = []
        for i, (age_from, age_to, rate_map) in enumerate(rates):
            ax = fig.add_subplot(gs[1, 2 * i + 1: 2 * i + 3])
            draw_missing_checkerboard(ax, np.shape(rate_map))
            im_rate = ax.imshow(rate_map, origin="lower", cmap=_rate_cmap(), interpolation='none',
                                norm=_rate_norm())
            setup_axes(ax, f"{age_from} → {age_to}", left=(i == 0))
            rate_axes.append(ax)
        fig.colorbar(im_rate, ax=rate_axes, location="bottom", shrink=min(1.0, 3 / len(rates)),
                     label="Thickness change rate (mm/year)", extend="both")

    outname = f"{alias.replace(' ', '_')}_{laterality}.progression.svg"
    fig.savefig(f"{outdir}/{outname}")
    plt.close(fig)
    print(f"wrote {outdir}/{outname}")
