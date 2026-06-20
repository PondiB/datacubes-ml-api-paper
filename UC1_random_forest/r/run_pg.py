"""Submit the UC1 random forest process graph to an openEOcubes backend."""

from __future__ import annotations

import os
import time
from pathlib import Path

import openeo


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def normalize_host(raw_host: str) -> str:
    if raw_host.startswith(("http://", "https://")):
        return raw_host
    return f"http://{raw_host}"


def connect_with_retry(
    host: str,
    user: str,
    password: str,
    *,
    attempts: int = 12,
    sleep_seconds: int = 5,
) -> openeo.Connection:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        print(f"Connection attempt {attempt}/{attempts}")
        try:
            connection = openeo.connect(url=host)
            connection.authenticate_basic(username=user, password=password)
            return connection
        except Exception as exc:  # noqa: BLE001 - retry until attempts exhausted
            last_error = exc
            if attempt < attempts:
                time.sleep(sleep_seconds)
    raise RuntimeError(
        f"Failed to connect/login to backend '{host}' after {attempts} attempts: {last_error}"
    ) from last_error


def main() -> None:
    host = normalize_host(env("OPENEO_HOST", "http://127.0.0.1:8000"))
    user = env("OPENEO_USER", "user")
    password = env("OPENEO_PASSWORD", "password")
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    default_pg = Path(__file__).resolve().parent / "full_pg.json"
    process_graph = Path(os.environ.get("PROCESS_GRAPH", default_pg))
    if not process_graph.is_file():
        raise SystemExit(f"Process graph not found: {process_graph}")

    print(f"Connecting to openEO backend at: {host}")
    connection = connect_with_retry(host, user, password)

    print(f"Loading process graph from: {process_graph}")
    cube = connection.datacube_from_json(str(process_graph))

    output_file = output_dir / "result.tif"
    print(f"Submitting batch job (output -> {output_file})")
    job = cube.create_job(title="UC1 random forest (openEOcubes)")
    job.start_and_wait()
    assets = job.get_results().get_assets()
    raster_assets = [a for a in assets if a.name.endswith((".tif", ".tiff", ".gtiff"))]
    if not raster_assets:
        raise RuntimeError(
            f"No raster result asset found. Available assets: {[a.name for a in assets]}"
        )
    raster_asset = raster_assets[0]
    print(f"Downloading result asset: {raster_asset.name}")
    output_file.write_bytes(raster_asset.load_bytes())
    print(f"Done. Result saved to {output_file}")


if __name__ == "__main__":
    main()
