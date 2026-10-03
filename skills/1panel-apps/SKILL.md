---
name: 1panel-apps
description: Inspect installed 1Panel apps or explicitly install MySQL/OpenResty using the pinned official MCP; use with confirmed names, supported versions, ports and credential handling.
license: Apache-2.0
---

# 1Panel Applications

## When to use
Inspect installed apps or install precisely MySQL/OpenResty. The pinned MCP is not a generic app store installer or upgrade manager.

## How to use this skill
1. Read [operation contract](references/operation-contract.md). list_installed_apps uses `{}`. Check existing identity/type/status and report the 500-item limit.
2. For an authorized install, check dependencies and port conflicts using available evidence. Missing port inspection requires manual confirmation, not a made-up tool. Installation requires configured full access and bounded user authorization.
3. MySQL: resolve `name`, explicit supported `version` (not `latest`), `port` (default 3306) and private `root_password` handling. Default-generated password is not guaranteed to be returned; don't promise recovery. Do not expose passwords in summaries.
4. OpenResty: resolve `name`, `http_port`/`https_port` (default 80/443). The server selects its version internally; an exact-version requirement cannot be satisfied through this tool. Stop rather than silently install a different version.
5. Submit once. Re-list and check actual installation state; API task acceptance is not proof the container is healthy or network services are reachable. No automatic retries on unknown outcomes, uninstall or rollback.

## Best practices
No arbitrary app installation, Docker control or upgrades are available. [Tool reference](references/tools.md).

## Keywords

1Panel, MCP, apps, server administration
