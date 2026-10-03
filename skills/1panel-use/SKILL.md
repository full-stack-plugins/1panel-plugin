---
name: 1panel-use
description: Route 1Panel management requests to connection setup, read-only inspection, website, certificate, database, application or scoped security skills using the actual available MCP tools.
license: Apache-2.0
---

# 1Panel

## When to use
Manage or inspect a user's existing 1Panel server. This package is a community integration with the official MCP service, not a panel installer.

## How to use this skill
1. Resolve the user's target and available MCP connection. If unconfigured, use `1panel-setup`; do not infer a host or ask for its key in chat.
2. Route: system health → `1panel-system`; sites → `1panel-websites`; SSL → `1panel-certificates`; databases → `1panel-databases`; OpenResty/MySQL installs → `1panel-apps`; bounded risk review → `1panel-security-audit`.
3. Discover the session tools and parameters. Read the [capability reference](references/tools.md) and [operation contract](references/operation-contract.md) before writes.
4. Start with reads. Preserve existing specific authorization, identify material missing parameters and stop for unsupported prerequisites. Do not chain a read request into installation.
5. Summarize actual results and limits; hand off to one specialist without inventing new state, capabilities or approval.

## Best practices
Manual panel features and MCP tools are distinct. A missing tool is not a request to use SSH or raw API access. Do not claim broad full-panel control.

## Keywords

1Panel, MCP, use, server administration
