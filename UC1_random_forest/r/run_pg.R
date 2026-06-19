library(jsonlite)
library(httr2)
library(openeo)

env_with_default <- function(name, default) {
  value <- Sys.getenv(name, unset = default)
  if (!nzchar(value)) default else value
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
    trial <- try(
      connect(host = host, user = user, password = password),
      silent = TRUE
    )
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

host <- normalize_host(env_with_default("OPENEO_HOST", "http://127.0.0.1:8000"))
user <- env_with_default("OPENEO_USER", "user")
password <- env_with_default("OPENEO_PASSWORD", "password")
output_dir <- env_with_default("OUTPUT_DIR", "./results")
process_graph_path <- env_with_default("PROCESS_GRAPH", "full_pg.json")

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

if (!file.exists(process_graph_path)) {
  stop(sprintf("Process graph not found: %s", process_graph_path), call. = FALSE)
}

message(sprintf("Connecting to openEO backend at: %s", host))
connect_with_retry(host = host, user = user, password = password)

message(sprintf("Loading process graph from: %s", process_graph_path))
pg_json <- read_json(process_graph_path, simplifyVector = FALSE)

output_file <- file.path(output_dir, "result_r.tif")
timeout_seconds <- as.numeric(Sys.getenv("OPENEO_TIMEOUT_SECONDS", unset = "86400"))
if (!is.finite(timeout_seconds) || timeout_seconds < 60) {
  timeout_seconds <- 86400
}

message(sprintf(
  "Submitting synchronous job via /result (timeout %ds, output -> %s)",
  timeout_seconds,
  output_file
))
resp <- request(paste0(host, "/result")) |>
  req_auth_basic(user, password) |>
  req_body_json(list(process = list(process_graph = pg_json))) |>
  req_timeout(timeout_seconds) |>
  req_error(is_error = function(r) resp_status(r) >= 400) |>
  req_perform()

content_type <- resp_header(resp, "Content-Type")
if (!is.na(content_type) && grepl("application/json", content_type, fixed = TRUE)) {
  stop(resp_body_string(resp), call. = FALSE)
}

writeBin(resp_body_raw(resp), output_file)
message(sprintf("Done. Result saved to %s", output_file))
