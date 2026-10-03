# 1Panel Plugin Architecture

Version 0.1.0, local implementation. The boundary integrates official mcp-1panel v1.0.0; it does not reimplement the panel API or claim to be an official plugin.

## Ownership and trust

| Component | Owner / implementation |
|---|---|
| Operation routing and domain constraints | Eight original source skills from 1panel-skills |
| Portable discovery | Root plugin.json + standard mcp.json |
| Private connection setup | scripts/setup_connection.py, user-triggered only |
| Stdio policy and framing | scripts/panel_proxy.py, Python standard library |
| API schemas, authentication and requests | Externally built official mcp-1panel at the reviewed commit |
| Live resource identity and authorization | User's selected panel and explicit bounded task |

```mermaid
sequenceDiagram
    participant U as User / Client
    participant P as Plugin stdio boundary
    participant O as Official MCP process
    participant A as 1Panel API
    U->>P: initialize (opaque request ID)
    P->>O: initialize (mapped internal ID)
    O-->>P: Actual capabilities/version
    P-->>U: Tool-only capabilities; original ID
    U->>P: tools/list
    P->>O: tools/list
    O-->>P: Official schemas
    P-->>U: Filtered allowed tool schemas
    U->>P: tools/call with bounded parameters
    alt Tool restricted or unknown
        P-->>U: Tool error; no official/API call
    else Allowed and initialized
        P->>O: Call once; no automatic retry
        O->>A: Signed API request
        A-->>O: API result
        O-->>P: Actual tool result
        P-->>U: Original ID and key-redacted result
    end
```

## Configuration and lifecycle

Only the explicit private data directory determines configuration. connection.json has binary path/SHA256, panel origin, access_level and reviewed upstream_commit; credentials.json contains the private panel key. No inherited PANEL variable selects the target. Standard mcp.json supplies `${PLUGIN_DATA}`. Native adapters need explicit private path configuration if their loader lacks those variables.

The pinned executable is SHA256-checked on startup. Credentials go into its environment, not arguments; logs are contained in the private runtime working directory. This is integrity checking against user-verified settings, not signed publisher verification or OS sandboxing. The source builder pins a real release commit, uses an existing compiler and refuses implicit Go upgrades or overwriting an existing binary.

Each client connection starts one official stdio process. The boundary maps client request IDs to internal IDs, bounds framing at 1 MiB and in-flight requests at 32, and applies a 60-second request deadline. Supported client lifecycle/tool methods are initialize, initialized, ping, tools/list, tools/call and cancellation. Server-initiated sampling/elicitation/roots access is not advertised or supported. EOF/exit terminates the child; pending tool outcomes may be unknown. No persistent approval ledger is created.

## Permission, retry and rollback

Readonly (six reads) is default, readwrite adds three creates, full adds two installs. Unknown tool names remain denied even if upstream adds them. Discovery filtering and call-time checks are executable and tested separately. Skill guidance still checks user authorization and exact target; transport availability is not blanket consent, authentication or panel RBAC.

No retries are automatically submitted. A deadline, cancellation or child loss is not proof a write did not occur. Return unknown, reconcile the resource with reads or manual panel inspection, then decide the next action. No automatic delete/rollback is invented. Missing/malformed setup has a nonsecret startup diagnostic and disables only this MCP connection; skills remain usable as instructions.

## Evaluation and remaining deployment evidence

Tests run the actual pinned official executable through this proxy against a loopback simulated API. They cover all 11 tool calls, three discovery levels, direct policy bypass attempts, hashed panel authentication, actual API routes, reflected-key redaction, validation failures and unknown timeout outcomes. The simulated API does not prove a production 1Panel deployment, ACME issuance, real application install or installed-client behavior.

Package tests additionally verify static schema, source hashes, links and relocation. Source version publication and user-installed acceptance remain separate. See verification.md for actual local results and README.md for reproducible commands.
