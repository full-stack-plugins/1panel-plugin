---
name: 1panel-system
description: Inspect 1Panel system and dashboard information without mutations; use for host identity, resource observations, application counts and bounded health diagnosis.
license: Apache-2.0
---

# 1Panel System Inspection

## When to use
Identify a panel-managed host or perform a read-only health inspection.

## How to use this skill
1. Read the [operation contract](references/operation-contract.md) and discover get_system_info/get_dashboard_info.
2. Query `{}` for both; verify host identity before interpreting metrics. Capture timestamp and actual observed CPU/memory/disk/load values where returned. Never fill absent metrics with zero or assume live history exists.
3. Correlate counts with list_installed_apps/list_websites only when relevant. List failures do not justify installs or service restarts.
4. Report observations, possible causes and missing evidence separately. Logs, process management, service restart, SSH and historical monitoring are not available through the pinned MCP.

## Best practices
A healthy API response is not a complete server audit. A resource threshold is a signal to investigate, not proof of root cause. [Tool limits](references/tools.md).

## Keywords

1Panel, MCP, system, server administration
