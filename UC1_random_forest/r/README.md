# Use Case 1: Random Forest (openEOcubes)

This workflow runs the pre-built openEO process graph in [`full_pg.json`](full_pg.json) against a local [openEOcubes](https://github.com/PondiB/openEOcubes) backend.

The graph trains a random forest on Sentinel-2 L2A reflectance and writes a classified GeoTIFF via `save_result`.

## Quick start (Docker Compose)

From this directory:

```bash
docker compose down
docker compose up --build
```

For a clean backend workspace, run `docker compose down` before each full job. Pull the latest backend image when openEOcubes has been updated on Docker Hub:

```bash
docker compose pull openeocubes-backend
```

The backend uses async job settings aligned with the working `examples/13-ml-process-graph` setup in openEOcubes (`OPENEO_ASYNC_JOB_TIMEOUT_SEC=3600`, `OPENEO_STALE_OUTPUT_FINALIZE_SEC=30`, `linux/amd64`). A full run typically takes **~40–45 minutes** (RF training plus GeoTIFF export).

To build the backend from a local openEOcubes checkout instead of `brianpondi/openeocubes`:

```bash
OPENEOCUBES_ROOT=/path/to/openeocubes docker compose -f docker-compose.yaml -f docker-compose.build.yaml build --no-cache
OPENEOCUBES_ROOT=/path/to/openeocubes docker compose -f docker-compose.yaml -f docker-compose.build.yaml up
```

If a previous build failed partway through, use `build --no-cache` so R dependency layers are rebuilt cleanly.

After the job finishes, check that `results/result.tif` has ~258,168 classified pixels before visualizing.

This starts:

- `openeocubes-backend` on host port `8000` (`brianpondi/openeocubes`)
- `uc1-random-forest-runner`, which uses the [openeo Python client](https://open-eo.github.io/openeo-python-client/) to submit `full_pg.json` and download results to `./results/`

Default openEOcubes credentials:

- **Username:** `user`
- **Password:** `password`

Override with environment variables if needed:

```bash
OPENEO_USER=user OPENEO_PASSWORD=password docker compose up
```

## Python client (`run_pg.py`)

Local run (with openEOcubes already running on port 8000):

```bash
uv sync
uv run run_pg.py
```

Output is written to `./results/result.tif`.

## Visualize result (`visualize.py`)

After the job finishes:

```bash
uv run visualize.py
```

Saves a crop-type map to `./results/crop_map.pdf` and `./results/crop_map.png`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENEO_HOST` | `http://127.0.0.1:8000` (Compose) | openEO API URL |
| `OPENEO_USER` | `user` | Basic auth username |
| `OPENEO_PASSWORD` | `password` | Basic auth password |
| `PROCESS_GRAPH` | `./full_pg.json` | Path to the flat process graph JSON |
| `OUTPUT_DIR` | `./results` | Directory for downloaded job results |
| `OPENEO_PORT` | `8000` | Host port mapped to the backend (Compose only) |
| `OPENEO_ASYNC_JOB_TIMEOUT_SEC` | `3600` | Backend async job timeout (Compose backend only) |
| `OPENEO_STALE_OUTPUT_FINALIZE_SEC` | `30` | Backend stale-output finalize window (Compose backend only) |

## Compare with the Python/dask-ml path

After both workflows finish, use [`../compare`](../compare) to plot and compare the openEOcubes result against the openeo-processes-dask-ml output from [`../python`](../python).

## Requirements

- Docker with Compose enabled (for the bundled stack)
- For local Python runs: [uv](https://docs.astral.sh/uv/)
- Sufficient CPU/RAM for Sentinel-2 download, cube processing, and RF training (allow **~40–45 minutes** per Docker Compose job)
