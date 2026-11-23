import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FFMpegWriter

from oct_utils.plotting import draw_missing_checkerboard


def make_progression_video(ages: list[float], maps: list[np.ndarray], seconds: float, n_points: int, outname: str,
                           hold: float = 0, label: str = "Caucasian Reference"):
    """ Linearly interpolate the thickness maps in age and write them out as an mp4.
        Frames are evenly spaced in age, so the video time is proportional to the age difference.
        The last frame is held for `hold` seconds, so the video rests at the final age instead of
        appearing to jump straight back to the start."""
    ages = np.asarray(ages, dtype=float)
    stack = np.stack(maps)  # (n_ages, rows, cols)
    frame_ages = np.linspace(ages[0], ages[-1], n_points)

    def interpolated_map(age: float) -> np.ndarray:
        i = min(np.searchsorted(ages, age, side="right") - 1, len(ages) - 2)
        t = (age - ages[i]) / (ages[i + 1] - ages[i])
        return (1 - t) * stack[i] + t * stack[i + 1]

    # same look as plot_thickness_map
    fig, ax = plt.subplots()
    draw_missing_checkerboard(ax, stack.shape[1:])
    img = ax.imshow(stack[0], origin="lower", cmap='YlOrRd_r', interpolation='none', vmin=0.12, vmax=0.38)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0, -0.02, "Temporal", transform=ax.transAxes, ha="left", va="top")
    ax.text(1, -0.02, "Nasal", transform=ax.transAxes, ha="right", va="top")
    ax.text(-0.02, 0, "Inferior", transform=ax.transAxes, ha="right", va="bottom", rotation=90)
    ax.text(-0.02, 1, "Superior", transform=ax.transAxes, ha="right", va="top", rotation=90)
    fig.colorbar(img, label="Avg thickness (mm)")
    title = ax.set_title("")

    fps = n_points / (seconds - hold)
    writer = FFMpegWriter(fps=fps)
    with writer.saving(fig, outname, dpi=150):
        for age in frame_ages:
            img.set_data(interpolated_map(age))
            title.set_text(f"{label}, age {age:.1f}")
            writer.grab_frame()
        # freeze on the final map
        for _ in range(round(hold * fps)):
            writer.grab_frame()
    plt.close(fig)
    print(f"wrote {outname}")
