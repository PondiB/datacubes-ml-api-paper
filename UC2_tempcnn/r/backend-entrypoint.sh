#!/bin/bash
set -euo pipefail

# callr::r_bg() defaults to system_profile=FALSE and user_profile="project",
# so job workers ignore R_PROFILE_USER and sit defaults to ~75% of CPU cores.
# Patch the installed package once per container start and load site + user profiles.
RPROFILE_SITE=/etc/R/Rprofile.site
MARKER="# openeocraft-ml-showcase"
if ! grep -q "$MARKER" "$RPROFILE_SITE" 2>/dev/null; then
  cat >>"$RPROFILE_SITE" <<EOF
$MARKER
source("/etc/openeocraft/Rprofile")
EOF
fi

JOBS_R="/opt/dockerfiles/R/jobs.R"
if [[ ! -f "$JOBS_R" ]]; then
  JOBS_R="$(Rscript -e 'cat(system.file("R/jobs.R", package="openeocraft"))' 2>/dev/null || true)"
fi
if [[ -n "$JOBS_R" && -f "$JOBS_R" ]] && ! grep -q 'system_profile = TRUE' "$JOBS_R"; then
  sed -i 's/poll_connection = FALSE/poll_connection = FALSE, system_profile = TRUE, user_profile = TRUE/' "$JOBS_R"
fi

exec Rscript /opt/dockerfiles/docker/server.R
