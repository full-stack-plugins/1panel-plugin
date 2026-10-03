---
name: 1panel-setup
description: Set up or diagnose a 1Panel MCP connection using a pinned official executable and private plugin data; use for authentication, missing tools, transport and configuration problems.
license: Apache-2.0
---

# 1Panel Setup

## When to use
Connect an existing panel, diagnose missing or unauthorized tools, or change a user's explicitly chosen access level.

## How to use this skill
1. Locate the installed plugin and the writable data directory supplied by its client. Portable clients expose `PLUGIN_DATA`; native adapters may require the user to configure an absolute data path. Do not guess HOME/APPDATA or write private settings into the plugin.
2. Check existing configuration locally without printing credentials. Do not overwrite settings without explicit replacement intent. No installation runs on plugin load.
3. This integration pins official mcp-1panel v1.0.0, commit a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c. An existing Go 1.25+ compiler and Git can build it via the plugin's `scripts/build_official.py`; this explicit helper uses GOTOOLCHAIN=local and never upgrades Go. Building obtains project dependencies. Review instructions before running, and do not install missing tools silently.
4. After the user verifies the panel origin, enables its API interface and restricts allowed API source addresses in panel settings, run the explicit `scripts/setup_connection.py` with the data directory, binary path, verified binary SHA256, HTTPS host and requested access level. The key goes into its hidden local prompt. This reusable skill does not include the plugin scripts: standalone installation requires an equivalent trusted client configuration and must not pretend those scripts are present.
5. Readonly is the default. Readwrite adds three create tools; full adds MySQL/OpenResty installation. Availability is not per-operation authorization. Changes require reconnection.
6. Initialize MCP, discover tools, and call get_system_info against the intended target. Record connection success separately from functional API success. Authentication failures can reflect API enablement, source allowlist, key, clock or target; inspect those safely before repeated requests.

## References
[Capabilities and version limits](references/tools.md); [operation contract](references/operation-contract.md). HTTPS certificate failures require a trusted endpoint/certificate, not disabling verification. The release does not safely expose a remote HTTP deployment through this plugin; stdio is intentional.

## Best practices

Use the actual discovered tool schema, preserve specific authorization, keep secrets private, and verify observed outcomes without inventing capabilities.

## Keywords

1Panel, MCP, setup, server administration
