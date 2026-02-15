# HA Governance Troubleshooting

## Policy file not found

- Ensure `/config/policies.yaml` exists or set `policy_path` in the UI.

## UI flow missing

- Install version `>= 0.1.3`.
- Restart Home Assistant after updating.

## Changes not applied

- After editing policies, restart Home Assistant or wait a short time.
- Changing `policy_path` in the UI triggers an automatic reload.
