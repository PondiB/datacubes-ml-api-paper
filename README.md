# openEO ML Showcase

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](UC1_random_forest/r)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](UC1_random_forest/r)
[![R](https://img.shields.io/badge/R-4.2+-276DC3?logo=r&logoColor=white)](UC2_tempcnn/r)
[![openEO](https://img.shields.io/badge/openEO-API-0099CC)](https://openeo.org/)
[![uv](https://img.shields.io/badge/uv-managed-DE5FE9)](https://docs.astral.sh/uv/)

Examples for ML workflows on Earth observation datacubes using the openEO client API: training, inference, and embedding-style outputs. Each use case is self-contained under its folder with Docker (and Compose where noted).

## Use cases

| Path | Summary |
|------|---------|
| [`UC1_random_forest/python`](UC1_random_forest/python) | Random Forest on Sentinel-2 L2A reflectance for crop-type classification (GeoTIFF results). Run: `docker compose up --build` from that directory. |
| [`UC1_random_forest/r`](UC1_random_forest/r) | Same UC1 graph via openEOcubes (Python client). Run: `docker compose up --build` from that directory (~40–45 min). Test login: `user` / `password`. |
| [`UC2_tempcnn/r`](UC2_tempcnn/r) | TempCNN in R via `brianpondi/openeocraft`; Compose runs a local backend and the R job. Test login: `brian` / `123456`. See README for ports and Docker resource sizing. |
| [`UC3_embeddings`](UC3_embeddings) | Terramind foundation model: EO datacube → embeddings datacube (Zarr output, CPU inference). Run: `docker compose up --build` from that directory. |

Details, warnings, and exact commands live in each folder’s README.

## Requirements

Docker with Compose enabled. For UC2’s local Compose stack, the README documents test credentials (`brian` / `123456`) and how to allocate more CPU/RAM in Docker Desktop for long TempCNN jobs.

## License

See [LICENSE](LICENSE).
