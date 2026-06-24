# Limit sits parallel workers inside the backend container.
# Job workers are spawned with callr::r_bg(), which skips R_PROFILE_USER unless
# system_profile/user_profile are enabled (see backend-entrypoint.sh).
options(openeocraft.resource_fraction = 0.25)
options(openeocraft.multicores_max = 1L)
