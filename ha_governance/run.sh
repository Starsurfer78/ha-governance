#!/usr/bin/with-contenv bashio
# ==============================================================================
# Start HA Governance
# ==============================================================================

bashio::log.info "Starting HA Governance v0.1.47..."

cd /app || bashio::exit.nok "Cannot change to /app directory"

exec python3 -u main.py
