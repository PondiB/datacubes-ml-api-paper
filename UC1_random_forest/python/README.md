# Use Case 1: Random Forest

In this example, we use we train a Random Forest classifier on Sentinel-2-L2A reflectance values to map different crop types.
The python script which is executed in the container can be found 
[here](https://github.com/Open-EO/openeo-processes-dask-ml/blob/paper-embeddings-uc/examples/make_embeddings.py).
The corresponding R script can be found here.

Run it with `docker compose up --build`

The classified images are stored as GeoTIFFs to the results directory..

### Warning

- When running the container, you will see the following warning.
`Did not load machine learning processes due to missing dependencies: Install them like this: pip install openeo-processes-dask[implementations, ml]`.
This can be ignored, as this refers to the legacy ML processes implemented in `openeo-processes-dask` which our contribution aims 
to replace in `openeo-processes-dask-ml`.
