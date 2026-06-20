"""
Crop type map for the openEOcubes UC1 classification result.

Produces crop_map.pdf and crop_map.png in the results directory.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
RESULT_RASTER = RESULTS_DIR / "result.tif"
MAP_PDF = RESULTS_DIR / "crop_map.pdf"
MAP_PNG = RESULTS_DIR / "crop_map.png"

CLASS_NAMES = [
    "Barley",
    "Corn",
    "Permanent meadows",
    "Rapeseed",
    "Temporary meadows",
    "Wheat",
]
COLORS = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f"]
N = len(CLASS_NAMES)

cmap = ListedColormap(COLORS)
norm = BoundaryNorm(boundaries=np.arange(0.5, N + 1.5), ncolors=N)


def fmt_lon(x, _):
    return f"{abs(x):.2f}°{'W' if x < 0 else 'E'}"


def fmt_lat(y, _):
    return f"{y:.2f}°N"


def main() -> None:
    if not RESULT_RASTER.is_file():
        raise SystemExit(f"Result raster not found: {RESULT_RASTER}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(RESULT_RASTER) as src:
        data = src.read(1).astype(float)
        bounds = src.bounds
        extent = (bounds.left, bounds.bottom, bounds.right, bounds.top)

    data[data <= 0] = np.nan
    valid = int(np.sum(np.isfinite(data)))
    if valid == 0:
        raise SystemExit(f"No valid class pixels in {RESULT_RASTER}")

    lat_mid = (extent[1] + extent[3]) / 2
    geo_aspect = 1.0 / np.cos(np.radians(lat_mid))

    fig, ax = plt.subplots(figsize=(7.2, 5.4), layout="constrained")

    ax.imshow(
        data,
        cmap=cmap,
        norm=norm,
        extent=[extent[0], extent[2], extent[1], extent[3]],
        aspect=geo_aspect,
        interpolation="nearest",
    )
    ax.set_xlim(extent[0], extent[2])
    ax.set_ylim(extent[1], extent[3])
    ax.text(
        0.008,
        0.985,
        "openEOcubes crop-type classification",
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        va="top",
        ha="left",
        zorder=5,
        bbox=dict(
            facecolor="white",
            edgecolor="none",
            alpha=0.75,
            pad=2.5,
            boxstyle="round,pad=0.25",
        ),
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_lon))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(6))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_lat))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(4))
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.tick_params(axis="both", labelsize=8, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)

    patches = [
        mpatches.Patch(
            facecolor=COLORS[i],
            edgecolor="#444",
            linewidth=0.5,
            label=CLASS_NAMES[i],
        )
        for i in range(N)
    ]
    fig.legend(
        handles=patches,
        loc="lower center",
        ncol=N,
        bbox_to_anchor=(0.5, -0.08),
        fontsize=8.5,
        title="Crop type",
        title_fontsize=8.5,
        frameon=True,
        framealpha=0.97,
        edgecolor="#999",
        handlelength=1.1,
        handleheight=0.8,
        columnspacing=0.6,
        borderpad=0.3,
        handletextpad=0.35,
        labelspacing=0.1,
    )

    fig.savefig(MAP_PDF, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(MAP_PNG, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved {MAP_PDF} and {MAP_PNG} ({valid:,} classified pixels)")


if __name__ == "__main__":
    main()
