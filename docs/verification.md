# Local verification record

Scope: local implementation and real official-MCP protocol integration against a simulated panel endpoint. No production panel, real key or installed client was used.

| Check | Actual result | Evidence boundary |
|---|---|---|
| Agent Plugins 1.0.0 static checks | PASS, 8 skills and standard mcp.json | Static portable configuration/discovery |
| Package-local links and source hashes | PASS | Complete referenced snapshot resources |
| Policy/configuration unit tests | PASS, 5 | Read/write/install separation, unknown-tool denial, HTTPS origin and binary digest guards |
| Package snapshot tests | PASS, 2 | Relocation and deliberate changed-source detection |
| Official-MCP integration suite | PASS, 7 | Real official process, shipped proxy, loopback simulated API |
| Tool execution | All 11 tools exercised | Actual official schemas and routes; not real service provisioning |
| Three access levels | PASS | 6/9/11 tools discovered; direct restricted calls never reach API |
| Authentication and secrets | PASS | Official hashed API headers; quote/backslash-containing reflected test key redacted |
| Unknown mutation outcome | PASS | Deadline reported unknown; one API submission, no automatic retry |
| Reusable source package | PASS, 8 skills and 3 regressions | Bilingual catalog, metadata, references, relocation and failure detection |

Official source: v1.0.0 at a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c. The locally built Windows executable was compiled with Go 1.25.3; its build receipt records SHA256 d6a829b6b00b5285cf2552fb65cb71a9f6d6fbd9871def3ffcb2d670a23b58f6. Other platforms/builds have their own binary hashes. No official binary or private runtime configuration is included in the plugin archive.

Test invocation requires ONEPANEL_TEST_BINARY; without it the seven integration tests are skipped. A narrow static-only result must not be presented as this integration evidence. The simulated endpoint validates actual transport/request behavior, not production 1Panel compatibility, external DNS/TLS/ACME, healthy containers or real database connectivity.

These local results were recorded before source publication. Current remote CI status is available in the repository's GitHub Actions page. Tagged release, marketplace registration, production-panel acceptance and user-installed-client loading remain separate. Native clients must explicitly configure private paths when they do not support the portable variables.

Release v0.1.1: all skills are source-managed by 1panel-skills v0.1.1; no plugin-local skill exception. Source-ownership and added-resource drift tests passed. Supported manifests and aggregate marketplace share version 0.1.1 and immutable installation ref v0.1.1. Actual client installation remains unverified.
