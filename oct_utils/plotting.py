

import numpy as np
from matplotlib import pyplot as plt

from oct_utils.data_structures import PosteriorPoleData


def plot_thickness_map(ppd: PosteriorPoleData, scratch_dir: str, thck_map: str="original"):
    plt.figure()
    plt.title(f"{ppd.alias}, {ppd.age_at_test} {ppd.laterality} ({thck_map})")
    df = ppd.pp_map if thck_map == "original" else ppd.interpolated_map
    plt.xticks(np.arange(8), np.arange(1, 9))
    plt.yticks(np.arange(8), np.arange(1, 9))
    plt.imshow(df, origin="lower", cmap='RdYlBu', interpolation='none', vmin=0.12, vmax=0.38)
    plt.xlabel("Temporal-Nasal")
    plt.ylabel("Inferior-Superior")
    plt.colorbar(label="Avg thickness (mm)")  # Show color scale
    outname  = f"{ppd.alias.replace(' ', '_')}_{ppd.laterality}_"
    outname += f"{str(ppd.age_at_test).replace('.', '_')}.{thck_map}.png"
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
