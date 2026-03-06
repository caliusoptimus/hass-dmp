# Why I forked this repo:

I use this integration, it's fantastic, and thank you so much to everyone that has contributed!

That said, it seems to break often with updates. I'm having codex handle the problems so I can get back up and running.

# Summary of Changes from Codex

## Home Assistant 2026.3 compatibility and stability fixes

- Fixed options flow crash on HA 2026.3:
  - `OptionsFlow.config_entry` became read-only in newer HA.
  - Updated options flow handler to store its own `_config_entry` reference instead of assigning to `self.config_entry`.
  - Reason: prevent immediate options/reconfigure flow failure with `AttributeError`.

- Fixed options/reconfigure robustness with partial form submissions:
  - Updated options handling to tolerate missing optional add-zone fields.
  - Only adds a new zone when `zone_name`, `zone_number`, and non-default `zone_class` are all provided.
  - Reason: HA options forms may omit optional keys; previous code could crash or mis-handle input.

- Fixed listener lifecycle and unload/shutdown behavior:
  - `DMPListener.listen()` now stores the actual server object in `_server`.
  - `stop()` now safely handles already-stopped state and accepts optional event argument for HA stop callbacks.
  - `async_setup_entry` now ties update listeners and stop listeners to entry unload via `entry.async_on_unload(...)`.
  - Reason: avoid unload/reload crashes and callback signature mismatches that became more visible with newer HA/Python.

- Improved config-entry data handling for multi-entry safety:
  - Store listener per config entry (`hass.data[DOMAIN][entry_id][LISTENER]`) while preserving global fallback for backward compatibility.
  - Platform files now prefer per-entry listener and fall back to global listener.
  - Reason: reduce cross-entry interference without breaking existing setups.

- Fixed event parsing/state update bugs:
  - Trouble events now update trouble state (not bypass state).
  - Prevented possible uninitialized `areaState` usage in arming event branch.
  - Hardened status refresh path for empty/no-response cases.
  - Reason: improve state correctness and prevent runtime exceptions during packet handling.

## HA entity model alignment (low-risk, backward-compatible)

- Sensor status entity now exposes value through `native_value` (instead of overriding `state`).
  - Reason: align with HA `SensorEntity` recommendations and improve future compatibility.

- Removed manual device-registry deletion during sensor entity removal.
  - Reason: avoid unintended device removal side effects during reload/unload.

- Fixed invalid binary sensor fallback `device_class` (`None` instead of `"sensors"`).
  - Reason: `"sensors"` is not a valid HA binary sensor device class.

- Removed custom switch `device_class = "switch"` usage.
  - Reason: switch platform does not use device classes this way; remove invalid metadata.

- Corrected options selector mapping bug:
  - “Siren (Wired)” now maps to `wired_siren` (was incorrectly mapped to `wired_motion`).
  - Reason: prevent misclassification of configured zones.

## Test updates

- Updated listener tests to validate corrected server lifecycle behavior.
- Added options-flow regression coverage for missing optional fields.
- Reason: ensure the fixes above are protected against regressions.
