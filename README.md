# Pi WizLight Status Light

Use the existing WizLight controller as a visual status indicator for Pi.

## Requirements and installation

Install Python and `pywizlight` in the environment Pi can access:

```bash
python3 -m pip install pywizlight
```

```bash
INSTALL
pi install git:github.com/jimccann-rh/piwizlight && pi update --extensions
```

From this directory, install the Pi package:

```bash
pi install .
```

## Uninstall

From this directory, remove the package from Pi with:

```bash
pi remove .
```

This removes the package from Pi's settings; it does not delete this directory or its files.

The extension calls the bundled `pi_status_light.py` helper. It discovers a WizLight bulb on the configured network and caches its address in `~/blubip.txt`; the helper handles all bulb communication and color settings. If discovery fails, create `~/blubip.txt` manually with the bulb's IP address on one line:

```bash
printf '%s\n' '192.168.0.220' > ~/blubip.txt
```

Replace the example IP with your bulb's address.

## Status mapping

| Pi event | Status | Light |
|---|---|---|
| `session_start` | `input` | Green — ready |
| `agent_start` | `idle` | Yellow — processing |
| `tool_execution_start` | `working` | Red — tool executing |
| `tool_execution_end` for `write` or `edit` | `flash` | White |
| `agent_settled` | `input` | Green — ready |
| `session_shutdown` | `warm`, then `off` | Dim warm white, then off |

Pi does not expose a general permission-request lifecycle event. Red means a tool is executing; it does not necessarily mean Pi is waiting for approval. The white status remains until the next event changes it.
