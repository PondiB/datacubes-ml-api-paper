FROM rocker/r-ver:4.4

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    pkg-config \
    libabsl-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libudunits2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN Rscript -e "install.packages(c('openeo', 'jsonlite'), repos='https://cloud.r-project.org')"

WORKDIR /work

CMD ["Rscript", "/work/run_pg.R"]
