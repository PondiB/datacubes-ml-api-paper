# Agreement metrics

Per-pixel agreement between the UC1 classification rasters from openeo-processes-dask-ml
(`compare/data/result_python.gtiff`) and openEOcubes (`compare/data/result_r.tif`).

## Run

From this directory:

```bash
uv sync
uv run agreement.py
uv run figure5.py
```

- `agreement.py` prints accuracy, kappa, and Pontius metrics; saves `results/confusion_matrix.png`
- `figure5.py` saves side-by-side crop maps to `results/figure5.pdf` and `results/figure5.png`
