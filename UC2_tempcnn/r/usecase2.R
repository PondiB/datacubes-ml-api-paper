library(openeo)

require_env <- function(name) {
  value <- Sys.getenv(name, unset = "")
  if (!nzchar(value)) {
    stop(sprintf("Missing required environment variable: %s", name), call. = FALSE)
  }
  value
}

normalize_host <- function(raw_host) {
  if (grepl("^https?://", raw_host)) {
    raw_host
  } else {
    paste0("http://", raw_host)
  }
}

connect_with_retry <- function(host, user, password, attempts = 12, sleep_seconds = 5) {
  last_error <- NULL
  for (i in seq_len(attempts)) {
    message(sprintf("Connection attempt %d/%d", i, attempts))
    trial <- try({
      con <- connect(host = host)
      login(con = con, user = user, password = password)
    }, silent = TRUE)
    if (!inherits(trial, "try-error")) {
      return(trial)
    }
    last_error <- trial
    if (i < attempts) {
      Sys.sleep(sleep_seconds)
    }
  }
  stop(
    sprintf(
      "Failed to connect/login to backend '%s' after %d attempts. Last error: %s",
      host, attempts, as.character(last_error)
    ),
    call. = FALSE
  )
}

job_status <- function(job, con) {
  info <- describe_job(job, con = con)
  status_raw <- info$status
  if (is.null(status_raw)) "" else tolower(as.character(status_raw))
}

wait_until_job_terminal <- function(job, con, poll_sec, max_sec) {
  start <- Sys.time()
  repeat {
    status <- job_status(job, con = con)
    elapsed <- as.numeric(difftime(Sys.time(), start, units = "secs"))
    message(sprintf("[%.0fs] Job status: %s", elapsed, status))

    if (status %in% c("finished", "completed", "done")) {
      return(invisible(TRUE))
    }
    if (status %in% c("error", "failed")) {
      stop(sprintf("Job failed with status: %s", status), call. = FALSE)
    }
    if (status %in% c("canceled", "cancelled")) {
      stop(sprintf("Job was canceled: %s", status), call. = FALSE)
    }
    if (elapsed > max_sec) {
      stop(
        sprintf(
          "Timed out after %.0fs waiting for job (max JOB_MAX_WAIT_SECONDS=%s)",
          elapsed,
          max_sec
        ),
        call. = FALSE
      )
    }
    Sys.sleep(poll_sec)
  }
}

host <- normalize_host(require_env("OPENEO_HOST"))
user <- require_env("OPENEO_USER")
password <- require_env("OPENEO_PASSWORD")
output_dir <- Sys.getenv("OUTPUT_DIR", unset = "/work/results")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

poll_seconds <- as.numeric(Sys.getenv("JOB_POLL_SECONDS", unset = "30"))
max_wait_seconds <- as.numeric(Sys.getenv("JOB_MAX_WAIT_SECONDS", unset = "86400"))
if (!is.finite(poll_seconds) || poll_seconds < 1) {
  poll_seconds <- 30
}
if (!is.finite(max_wait_seconds) || max_wait_seconds < poll_seconds) {
  max_wait_seconds <- 86400
}

message(sprintf("Connecting to openEO backend at: %s", host))
connection <- connect_with_retry(host = host, user = user, password = password)

p <- processes(con = connection)

deforestation_data <-
  "https://github.com/e-sensing/sitsdata/raw/main/data/samples_deforestation_rondonia.rds"

tempcnn_model_init <- p$mlm_class_tempcnn(
  optimizer = "adam",
  epochs = 20,
  batch_size = 64
)

param_grid <- list(
  learning_rate = c(0.0005, 0.0001),
  epochs = c(20, 40)
)

message("Running TempCNN grid search (ml_tune_grid)...")
tempcnn_tuned <- p$ml_tune_grid(
  model = tempcnn_model_init,
  training_data = deforestation_data,
  target = "label",
  parameters = param_grid,
  scoring = "accuracy",
  cv = 0,
  seed = 42
)

tempcnn_model <- p$save_ml_model(
  data = tempcnn_tuned,
  name = "tempcnn_rondonia_tuned_v1",
  return_model = TRUE
)

extent_full <- list(west = -63.9, east = -62.9, south = -9.14, north = -8.14)
area_frac_raw <- Sys.getenv("UC2_SPATIAL_AREA_FRACTION", unset = "")
area_frac <- if (!nzchar(area_frac_raw)) {
  1
} else {
  suppressWarnings(as.numeric(area_frac_raw))
}
if (!is.finite(area_frac) || area_frac <= 0) {
  area_frac <- 1
}
if (area_frac >= 1) {
  spatial_extent <- extent_full
} else {
  lon_c <- (extent_full$west + extent_full$east) / 2
  lat_c <- (extent_full$south + extent_full$north) / 2
  lon_span <- extent_full$east - extent_full$west
  lat_span <- extent_full$north - extent_full$south
  k <- sqrt(area_frac)
  spatial_extent <- list(
    west = lon_c - lon_span * k / 2,
    east = lon_c + lon_span * k / 2,
    south = lat_c - lat_span * k / 2,
    north = lat_c + lat_span * k / 2
  )
}

temporal_extent <- c("2022-01-01", "2022-12-31")
cube_period <- Sys.getenv("UC2_REGULARIZE_PERIOD", unset = "P16D")
if (!nzchar(cube_period)) {
  cube_period <- "P16D"
}

res_raw <- Sys.getenv("UC2_GRID_RESOLUTION", unset = "30")
if (!nzchar(res_raw)) {
  res_raw <- "30"
}
resolution <- suppressWarnings(as.numeric(res_raw))
if (!is.finite(resolution) || resolution <= 0) {
  resolution <- 30
}

message(sprintf(
  "Inference cube: area fraction=%s, west=%.6f east=%.6f south=%.6f north=%.6f, period=%s, resolution=%gm",
  format(area_frac, scientific = FALSE, digits = 10),
  spatial_extent$west,
  spatial_extent$east,
  spatial_extent$south,
  spatial_extent$north,
  cube_period,
  resolution
))

band_spec <- trimws(Sys.getenv("UC2_COLLECTION_BANDS", unset = ""))
load_args <- list(
  id = "mpc-sentinel-2-l2a",
  spatial_extent = spatial_extent,
  temporal_extent = temporal_extent
)
if (nzchar(band_spec)) {
  band_list <- trimws(strsplit(band_spec, ",", fixed = TRUE)[[1]])
  band_list <- band_list[nzchar(band_list)]
  if (length(band_list)) {
    load_args$bands <- band_list
  }
}
if (is.null(load_args$bands)) {
  load_args$bands <- list(
    "B02", "B03", "B04", "B05", "B06", "B07", "B08",
    "B11", "B12", "B8A"
  )
}
datacube <- do.call(p$load_collection, load_args)

datacube <- p$cube_regularize(data = datacube, period = cube_period, resolution = resolution)
datacube <- p$ndvi(data = datacube, red = "B04", nir = "B08", target_band = "NDVI")

message("Running inference (ml_predict)...")
data <- p$ml_predict(data = datacube, model = tempcnn_model)

ml_job <- p$save_result(data = data, format = "GTiff")
job <- create_job(
  graph = ml_job,
  title = "TempCNN fine-tuning + inference",
  con = connection
)
job <- start_job(job, con = connection)

message("Submitted job successfully:")
print(job)

wait_until_job_terminal(
  job = job,
  con = connection,
  poll_sec = poll_seconds,
  max_sec = max_wait_seconds
)

download_job_asset <- function(host, user, job_id, asset, dest) {
  if (!requireNamespace("httr", quietly = TRUE) ||
      !requireNamespace("base64enc", quietly = TRUE)) {
    return(FALSE)
  }
  token <- base64enc::base64encode(charToRaw(user))
  url <- sprintf(
    "%s/files/jobs/%s/%s?token=%s",
    sub("/$", "", host),
    job_id,
    utils::URLencode(asset, reserved = TRUE),
    utils::URLencode(token, reserved = TRUE)
  )
  dest_dir <- dirname(dest)
  if (nzchar(dest_dir)) {
    dir.create(dest_dir, recursive = TRUE, showWarnings = FALSE)
  }
  resp <- httr::GET(url, httr::write_disk(dest, overwrite = TRUE))
  ok <- httr::status_code(resp) == 200L
  if (!ok && file.exists(dest)) {
    unlink(dest)
  }
  ok
}

convert_to_compatible_geotiff <- function(src, dest) {
  if (!file.exists(src)) {
    stop(sprintf("Source raster not found: %s", src), call. = FALSE)
  }
  if (!requireNamespace("terra", quietly = TRUE)) {
    file.copy(src, dest, overwrite = TRUE)
    return(invisible(dest))
  }
  raster <- terra::rast(src)
  terra::writeRaster(
    raster,
    dest,
    overwrite = TRUE,
    filetype = "GTiff",
    gdal = c("COMPRESS=LZW", "BIGTIFF=NO", "TILED=YES")
  )
  invisible(dest)
}

finalize_outputs <- function(job, host, user, output_dir) {
  job_id <- as.character(job$id)
  downloaded <- list.files(
    output_dir,
    pattern = "\\.tif$",
    full.names = TRUE,
    ignore.case = TRUE
  )
  if (!length(downloaded)) {
    warning("No GeoTIFF assets downloaded; skipping post-processing.", call. = FALSE)
    return(invisible(NULL))
  }

  class_src <- downloaded[grep("class", basename(downloaded), ignore.case = TRUE)]
  if (!length(class_src)) {
    class_src <- downloaded[[1]]
  } else {
    class_src <- class_src[[1]]
  }

  result_class <- file.path(output_dir, "result_class.tif")
  message(sprintf("Writing viewer-friendly GeoTIFF: %s", result_class))
  convert_to_compatible_geotiff(class_src, result_class)

  probs_dest <- file.path(output_dir, "result_probs.tif")
  start_date <- sub(".*class_(\\d{4}-\\d{2}-\\d{2}).*", "\\1", basename(class_src))
  if (!grepl("^\\d{4}-\\d{2}-\\d{2}$", start_date)) {
    start_date <- "2022-01-05"
  }
  prob_candidates <- unique(c(
    sprintf("temp/SENTINEL-2_MSI_20LMR_%s_2022-12-23_probs_v1.tif", start_date),
    "temp/SENTINEL-2_MSI_20LMR_2022-01-05_2022-12-23_probs_v1.tif"
  ))
  for (asset in prob_candidates) {
    if (download_job_asset(host, user, job_id, asset, probs_dest)) {
      message(sprintf("Downloaded probability raster: %s", probs_dest))
      convert_to_compatible_geotiff(probs_dest, probs_dest)
      break
    }
  }

  invisible(result_class)
}

run_visualization <- function() {
  viz_script <- Sys.getenv("UC2_VIZ_SCRIPT", unset = "/work/visualize.py")
  if (!file.exists(viz_script)) {
    viz_script <- file.path(getwd(), "visualize.py")
  }
  if (!file.exists(viz_script)) {
    message("visualize.py not found; skip map generation.")
    return(invisible(FALSE))
  }
  py <- Sys.which("python3")
  if (!nzchar(py)) {
    message("python3 not found; skip map generation.")
    return(invisible(FALSE))
  }
  status <- system2(py, c(viz_script), stdout = TRUE, stderr = TRUE)
  if (inherits(status, "character")) {
    cat(paste(status, collapse = "\n"), "\n")
  }
  invisible(TRUE)
}

message(sprintf("Job finished. Downloading results to %s", output_dir))
download_results(job = job, folder = output_dir, con = connection)
finalize_outputs(
  job = job,
  host = host,
  user = user,
  output_dir = output_dir
)
run_visualization()
message("Done.")
