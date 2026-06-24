# Use Case 2: TempCNN (R)

This use case runs the R openEO TempCNN workflow (hyperparameter tuning, training, and inference) against an openEO backend using the `brianpondi/openeocraft` Docker image.

The script (`usecase2.R`) builds a process graph that:

1. Tunes a TempCNN with `ml_tune_grid` on Rondonia deforestation samples
2. Saves the tuned model with `save_ml_model`
3. Loads Sentinel-2 L2A for a subset bbox, regularizes to `P16D` / **30 m** (configurable), computes NDVI
4. Runs `ml_predict`, submits a batch job, downloads GeoTIFF outputs, writes **`result_class.tif`** (classic GeoTIFF), optionally **`result_probs.tif`**, and builds **`deforestation_map.pdf`** / **`.png`**

## Why it sits on `cube_regularize`

Sentinel‑2 revisit times are **irregular**. `cube_regularize` **fills per-pixel time series** onto a fixed grid (`period`) and raster (`resolution`). With the default footprint — the **full Rondonia box** (~1° × 1°), **full year 2022**, **30 m**, **16‑day spacing** — the backend must read and synchronize a very large number of cube cells and time slices. That step is usually **much slower than training** because it is I/O‑ and memory‑heavy, not GPU‑friendly. Progress may look “stuck” while data is fetched and aggregated.

If **CPU stays at 0% for more than ~30 minutes** after downloads finish, the backend job may have **died** (zombie R workers) while the client keeps polling `running`. This often happens under Rosetta/amd64 emulation when `sits` forks many parallel R workers. The bundled `backend-entrypoint.sh` forces **single-core** sits workers and patches `callr` so job subprocesses load the site profile. Check `_stderr.log` in the job workspace (`multicores=` should be **1**, not 9). Restart with `docker compose down && docker compose up --abort-on-container-exit`.

The **Rondonia samples** used for training are built for a **regular 16‑day (`P16D`) timeline over a full seasonal year**. Keep inference aligned: **`cube_regularize`** uses **`P16D`** and **`2022-01-01` … `2022-12-31`** so time series lengths match **sits** expectations. Changing period or shortening the year without updating training data and the model risks mis‑aligned timelines.

Mitigations:

- Give Docker plenty of **CPU and RAM** (see **Docker resources** below); **exit `137`** often means memory pressure during this phase.
- The workflow loads ten Sentinel-2 bands plus NDVI for inference (`B02`–`B08`, `B8A`, `B11`, `B12`).

Grid search runs four combinations (`learning_rate` × `epochs`) before inference; allow several hours on CPU.

## Prerequisites

- Docker with Compose enabled

## Docker resources (recommended for speed)

Docker Desktop runs containers in a **Linux VM**. Training and cube work only use CPU/RAM allocated to that VM, so bump limits before long runs (**Settings → Resources**):

- **CPUs:** most cores you can spare (leave one or two for the host).
- **Memory:** TempCNN / `sits` / Torch benefit from **8 GB or more**; **12–16 GB** helps if your machine allows.
- **Apply & restart** Docker after changing limits.

Optional: enable **VirtioFS** file sharing (in Docker Desktop settings, name varies by version) for faster binds into `./results` and `/work`.

If **`openeocraft-backend` (or Compose) exits with code `137`**, the Linux kernel likely sent **SIGKILL** — often **out-of-memory** inside the Docker VM. Raise **Memory** in Docker Desktop Resources, close other heavy apps, and retry.

## Test credentials (local Compose)

The bundled `openeocraft-backend` is configured for local testing with:

- **Username:** `brian`
- **Password:** `123456`

Use other values only if your backend differs.

## Run with one command

From this directory (`UC2_tempcnn/r`):

```bash
docker compose up --abort-on-container-exit
```

Default credentials are `brian` / `123456` in `docker-compose.yaml`. Override if needed:

```bash
OPENEO_USER=brian OPENEO_PASSWORD=123456 docker compose up --abort-on-container-exit
```

This command starts:

- `openeocraft-backend` on host port `8001` (mapped to container `8000`)
- `uc2-tempcnn-r`, which executes `usecase2.R`, waits until the job reaches a terminal status, then downloads outputs into `./results`.

Default backend URL for the runner is `http://openeocraft-backend:8000`.
The backend advertises that same URL via `OPENEOCRAFT_API_BASE_URL` (required with the current openEOcraft image — without it, the R client follows `127.0.0.1` from capabilities and fails inside Compose).

Pull the amd64 image explicitly on Apple Silicon:

```bash
docker pull --platform linux/amd64 brianpondi/openeocraft:latest
```

Override with `OPENEO_HOST` if needed.

Optional environment variables for the runner:

- `JOB_POLL_SECONDS` — poll interval when checking job status (default `30`).
- `JOB_MAX_WAIT_SECONDS` — give up after this many seconds (default `86400`, one day).
- `UC2_SPATIAL_AREA_FRACTION` — fraction of the full Rondonia bbox (default `1` = full box; use `0.285714` for a faster ~2/7 subset).
- `UC2_GRID_RESOLUTION` — regularized raster resolution in metres (default `30`; use `300` for faster smoke tests).
- `UC2_REGULARIZE_PERIOD` — regularization period (default `P16D`).
- `UC2_COLLECTION_BANDS` — optional comma-separated band list override.
- `OPENEOCRAFT_CPU_LIMIT` / `OPENEOCRAFT_MEM_LIMIT` — backend container limits (default `8` CPUs, `16g` RAM).

## Outputs (`./results`)

| File | Description |
|------|-------------|
| `result_class.tif` | Viewer-friendly class map (classic GeoTIFF, LZW) |
| `result_probs.tif` | Class probability stack (when available from job workspace) |
| `deforestation_map.pdf` / `.png` | Publication-style land-cover map |
| `SENTINEL-2_*_class_*.tif` | Raw backend export (BigTIFF + ZSTD; may not open in Preview) |

Regenerate the map from an existing `result_class.tif`:

```bash
uv run visualize.py
# or: python3 visualize.py
```
