"""
Land-cover map for the UC2 TempCNN deforestation classification result.

Reads ``results/result_class.tif`` and writes ``deforestation_map.pdf`` and
``deforestation_map.png``.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from rasterio.crs import CRS
from rasterio.transform import array_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
RESULT_RASTER = RESULTS_DIR / "result_class.tif"
MAP_PDF = RESULTS_DIR / "deforestation_map.pdf"
MAP_PNG = RESULTS_DIR / "deforestation_map.png"

# Factor level order from samples_deforestation_rondonia.rds (sits training data).
CLASS_NAMES = [
    "Clear cut (bare soil)",
    "Clear cut (burned)",
    "Clear cut (vegetation)",
    "Forest",
    "Mountainside forest",
    "Riparian forest",
    "Seasonally flooded",
    "Water",
    "Wetland",
]
LEGEND_LABELS = [
    "Bare soil",
    "Burned",
    "Cut vegetation",
    "Forest",
    "Mountainside",
    "Riparian",
    "Flooded",
    "Water",
    "Wetland",
]
COLORS = [
    "#b35806",
    "#e08214",
    "#fdb863",
    "#1b7837",
    "#5aae61",
    "#a6dba0",
    "#92c5de",
    "#0571b0",
    "#762a83",
]
N = len(CLASS_NAMES)

cmap = ListedColormap(COLORS)
norm = BoundaryNorm(boundaries=np.arange(0.5, N + 1.5), ncolors=N)


def fmt_lon(x, _):
    return f"{abs(x):.2f}°{'W' if x < 0 else 'E'}"


def fmt_lat(y, _):
    return f"{abs(y):.2f}°{'S' if y < 0 else 'N'}"


def load_display_grid(path: Path) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Return class grid and geographic extent (left, bottom, right, top) in WGS84."""
    with rasterio.open(path) as src:
        data = np.asarray(src.read(1), dtype=np.float32)
        nodata = src.nodata
        src_crs = src.crs or CRS.from_epsg(4326)

        if src_crs.is_projected:
            dst_crs = CRS.from_epsg(4326)
            transform, width, height = calculate_default_transform(
                src_crs,
                dst_crs,
                src.width,
                src.height,
                *src.bounds,
            )
            out = np.full((height, width), np.nan, dtype=np.float32)
            reproject(
                source=data,
                destination=out,
                src_transform=src.transform,
                src_crs=src_crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                src_nodata=nodata,
                dst_nodata=np.nan,
                resampling=Resampling.nearest,
            )
            left, bottom, right, top = array_bounds(height, width, transform)
            return out, (left, bottom, right, top)

        return data, (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)


def main() -> None:
    if not RESULT_RASTER.is_file():
        raise SystemExit(f"Result raster not found: {RESULT_RASTER}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    data, extent = load_display_grid(RESULT_RASTER)
    data[(data < 1) | (data > N)] = np.nan

    valid = int(np.sum(np.isfinite(data)))
    if valid == 0:
        raise SystemExit(f"No valid class pixels in {RESULT_RASTER}")

    lat_mid = (extent[1] + extent[3]) / 2
    geo_aspect = 1.0 / np.cos(np.radians(lat_mid))

    fig = plt.figure(figsize=(9.0, 6.5), layout="constrained")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.34], wspace=0.08)
    ax = fig.add_subplot(gs[0, 0])
    leg_ax = fig.add_subplot(gs[0, 1])
    leg_ax.axis("off")

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
    ax.set_title(
        "TempCNN deforestation / land cover\nRondônia subset",
        fontsize=11,
        fontweight="bold",
        loc="left",
        pad=10,
    )
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_lon))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(5))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_lat))
    ax.yaxis.set_major_locator(mticker.MaxNLocator(4))
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.tick_params(axis="both", labelsize=8, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)

    present = sorted({int(v) for v in data[np.isfinite(data)]})
    patches = [
        mpatches.Patch(
            facecolor=COLORS[i - 1],
            edgecolor="#444",
            linewidth=0.5,
            label=LEGEND_LABELS[i - 1],
        )
        for i in present
    ]
    leg_ax.legend(
        handles=patches,
        loc="center left",
        fontsize=9,
        title="Land cover",
        title_fontsize=9.5,
        frameon=True,
        framealpha=0.97,
        edgecolor="#999",
        handlelength=1.2,
        handleheight=0.9,
        borderpad=0.6,
        labelspacing=0.55,
    )

    fig.savefig(MAP_PDF, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(MAP_PNG, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved {MAP_PDF} and {MAP_PNG} ({valid:,} classified pixels)")


if __name__ == "__main__":
    main()
