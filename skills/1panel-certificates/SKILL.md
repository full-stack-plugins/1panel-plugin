---
name: 1panel-certificates
description: Inspect 1Panel SSL certificates or request issuance through an existing ACME and DNS configuration; use for certificate inventory and explicitly authorized creation, not renewal or binding.
license: Apache-2.0
---

# 1Panel Certificates

## When to use
Inspect certificates and request a specific certificate supported by the pinned official server.

## How to use this skill
1. Read [operation contract](references/operation-contract.md); list_ssls uses `{}`. Inspect actual returned domains and expiry fields, preserving unknowns.
2. Before authorized create_ssl, confirm exact domain, DNS control and provider (`http` or `dnsAccount`). Existing ACME account is required; upstream chooses its first returned account and does not expose account selection. The user must verify this account in the panel. Stop if that selection is ambiguous or unacceptable.
3. DNS issuance needs an existing confirmed DNS account ID or exact name via `dns_account_id`/`dnsAccount`; do not guess one. HTTP challenge needs actual routing/port prerequisites. Creating ACME/DNS accounts is unsupported by MCP.
4. Submit once and re-list to check certificate identity and issuance state. A task accepted or pending certificate is not active TLS. Binding, renewal and external TLS checks are separate unsupported or explicitly authorized operations.

## Best practices
Never disclose private keys. Respect ACME rate limits; unknown outcomes require reconciliation before another request. [Tool reference](references/tools.md).

## Keywords

1Panel, MCP, certificates, server administration
