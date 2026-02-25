# Use official Python 3.11 image
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.2

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=2.1.3
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Configure Poetry to not create virtualenvs (install into container environment)
RUN poetry config virtualenvs.create false

# Set working directory
WORKDIR /app

# Clone the repository (replace with your repo URL)
RUN git clone https://github.com/Open-EO/openeo-processes-dask-ml.git

WORKDIR /app/openeo-processes-dask-ml
RUN git checkout class_mlm

# Install dependencies with extras --extras "torch onnx scikit-learn"
RUN poetry install --no-interaction --no-ansi --extras scikit-learn

# Default command (adjust as needed)
CMD ["python", "examples/train_rf.py"]

