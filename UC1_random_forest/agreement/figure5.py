"""
Figure 5 – Crop type maps for the Brittany prediction region.

Produces figure5.pdf and figure5.png in the results directory.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from rasterio.transform import array_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject

ROOT = Path(__file__).resolve().parent
COMPARE_DATA = ROOT.parent / "compare" / "data"
RESULTS_DIR = ROOT / "results"

PYTHON_GTIFF = COMPARE_DATA / "result_python.gtiff"
R_TIF = COMPARE_DATA / "result_r.tif"
FIGURE5_PDF = RESULTS_DIR / "figure5.pdf"
FIGURE5_PNG = RESULTS_DIR / "figure5.png"

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
    if not PYTHON_GTIFF.is_file():
        raise SystemExit(f"Python raster not found: {PYTHON_GTIFF}")
    if not R_TIF.is_file():
        raise SystemExit(f"R raster not found: {R_TIF}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(PYTHON_GTIFF) as src:
        dst_crs = "EPSG:4326"
        t4326, w4326, h4326 = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        py_data = np.full((h4326, w4326), 0, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1),
            destination=py_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=t4326,
            dst_crs=dst_crs,
            resampling=Resampling.nearest,
        )
        py_ext = array_bounds(h4326, w4326, t4326)

    py_data = py_data.astype(float)
    py_data[py_data <= 0] = np.nan

    with rasterio.open(R_TIF) as src:
        r_data = src.read(1).astype(float)
        bounds = src.bounds
        r_ext = (bounds.left, bounds.bottom, bounds.right, bounds.top)

    r_data[r_data <= 0] = np.nan

    lon0 = max(py_ext[0], r_ext[0])
    lat0 = max(py_ext[1], r_ext[1])
    lon1 = min(py_ext[2], r_ext[2])
    lat1 = min(py_ext[3], r_ext[3])

    lat_mid = (lat0 + lat1) / 2
    geo_aspect = 1.0 / np.cos(np.radians(lat_mid))
    map_ratio = (lon1 - lon0) * np.cos(np.radians(lat_mid)) / (lat1 - lat0)

    left_margin = 0.62
    right_margin = 0.05
    top_margin = 0.10
    bottom_margin = 0.38
    gap = 0.04
    legend_height = 0.46

    fig_w = 9.0
    plot_w = fig_w - left_margin - right_margin
    panel_h = plot_w / map_ratio
    fig_h = top_margin + 2 * panel_h + gap + bottom_margin + legend_height

    left_frac = left_margin / fig_w
    right_frac = 1 - right_margin / fig_w
    box_w = right_frac - left_frac
    box_h = panel_h / fig_h
    bottom_legend = legend_height / fig_h
    bottom_panel = bottom_legend + bottom_margin / fig_h
    top_panel = bottom_panel + box_h + gap / fig_h

    fig = plt.figure(figsize=(fig_w, fig_h))
    ax_a = fig.add_axes([left_frac, top_panel, box_w, box_h])
    ax_b = fig.add_axes([left_frac, bottom_panel, box_w, box_h])

    panels = [
        (ax_a, py_data, py_ext, "(a) openeo-processes-dask-ml", False),
        (ax_b, r_data, r_ext, "(b) openEOcubes", True),
    ]

    for ax, data, extent, label, show_x in panels:
        ax.imshow(
            data,
            cmap=cmap,
            norm=norm,
            extent=[extent[0], extent[2], extent[1], extent[3]],
            aspect=geo_aspect,
            interpolation="nearest",
        )
        ax.set_xlim(lon0, lon1)
        ax.set_ylim(lat0, lat1)
        ax.text(
            0.008,
            0.985,
            label,
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
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_lat))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(4))
        ax.set_ylabel("Latitude", fontsize=9)
        ax.tick_params(axis="both", labelsize=8, length=3)
        for spine in ax.spines.values():
            spine.set_linewidth(0.5)

        if show_x:
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_lon))
            ax.xaxis.set_major_locator(mticker.MaxNLocator(6))
            ax.set_xlabel("Longitude", fontsize=9)
        else:
            ax.xaxis.set_visible(False)

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
        bbox_to_anchor=(0.5, 0.0),
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

    fig.savefig(FIGURE5_PDF, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURE5_PNG, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved {FIGURE5_PDF} and {FIGURE5_PNG}")


if __name__ == "__main__":
    main()
