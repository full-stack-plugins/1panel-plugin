---
name: 1panel-databases
description: Inspect supported 1Panel database instances and create specifically authorized MySQL or PostgreSQL databases; use with explicit instance identities, exposure awareness and private credential handling.
license: Apache-2.0
---

# 1Panel Databases

## When to use
Inspect the supported database inventory or create a bounded database in an already installed instance. Not for SQL execution, migrations, backup, restore or deletion.

## How to use this skill
1. Read [operation contract](references/operation-contract.md). Resolve the exact installed database application/instance. list_databases `name` means that instance, not the SQL database to create. Its upstream search endpoint is MySQL-oriented; do not claim PostgreSQL inventory without actual evidence.
2. For create_database, resolve `database_type` (`mysql`/`postgresql`), `database` (existing instance), `name` (new SQL database), username and a private password-delivery workflow. Database installation is a distinct, authorized operation.
3. Upstream MySQL creation sets permission `%`; it cannot express a source-restricted account through this tool. Clearly explain that exposure. If the user's requirement is narrow source permissions, stop and use a separately authorized manual panel workflow rather than create a broader account. Do not treat base64 as encryption.
4. Upstream-generated passwords are not reliably returned for delivery; use a user-approved confidential password workflow or report this unsupported requirement. Avoid passwords in transcripts/receipts. Do not ask the user to paste secrets into chat.
5. Check relevant existing records, submit once, then use supported reads to verify identity. PostgreSQL verification may require panel UI. Never claim application connectivity or schema readiness from creation alone.

## Best practices
No automatic rollback by deletion. Timeouts need reconciliation. [Capability limits](references/tools.md).

## Keywords

1Panel, MCP, databases, server administration
