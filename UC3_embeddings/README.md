# Use Case 3: Embeddings Datacube

In this example, we use the Terramind Foundation model to transform a standard EO datacube (dimensions bands, time, x, y)
into a datacube of EO embeddings. The script that is running inside the container once it is built and started can be found
[here](https://github.com/Open-EO/openeo-processes-dask-ml/blob/paper-embeddings-uc/examples/make_embeddings.py).

We did not add GPU support to the container, therefore, prediction runs on the CPU and may take some time.

Run it with `docker compose up --build`

The resulting datacube of EO embeddings will be stored as a zarr file in the results directory.

### Warning

- Due to large required libraries (e.g. pytorch), this container is 15GB in size.
- When running the container, you will see the following warning.
`Did not load machine learning processes due to missing dependencies: Install them like this: pip install openeo-processes-dask[implementations, ml]`.
This can be ignored, as this refers to the legacy ML processes implemented in `openeo-processes-dask` which our contribution aims 
to replace in `openeo-processes-dask-ml`.
