# Security Policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository's **Security → Report a vulnerability** private-advisory flow. Include affected revision, deployment assumptions, impact, minimal reproduction details, and suggested mitigations when known. Remove credentials, private player data, and unnecessary exploit detail. Maintainers will acknowledge, triage, coordinate remediation, and publish disclosure timing according to risk and contributor availability; no fixed response SLA is promised at this early stage.

## System and scope

This policy covers the native Minecraft integration, observation/action schemas, agent runtime and persistence, model serving/training interfaces, memory and personal state, data/telemetry tooling, evaluation/simulation infrastructure, and operator controls in this repository.

Important assets include server integrity and availability; host credentials and files; private player chat/telemetry and consent records; world saves; agent identities, memories, relationships, and adapters; datasets and model artifacts; and trustworthy research results.

Deployment topology is not yet selected. Treat Minecraft servers, worlds, players, mods/plugins, resource packs, chat, signs/books, imported saves, datasets, checkpoints, model outputs, and network peers as potentially untrusted. Administrative operators and build/release systems are trusted only within explicitly granted capabilities.

## Threat model and trust boundaries

Primary boundaries are:

- Minecraft/world inputs → native integration and parsers;
- native observations/actions → agent runtime and model services;
- model-generated output → action validation, persistence, communication, and any experimental executable skill system;
- one agent's personal state/cache/adapter → every other agent;
- game/research processes → host filesystem, processes, credentials, and network;
- telemetry/player content → datasets, training, publications, and retained artifacts;
- administrator/operator APIs → world, agent, and data mutation.

Attackers may control protocol messages, malformed schemas, world data, chat or text content, model outputs, imported artifacts, timing/load, and ordinary player actions. Research convenience, a cooperative server, or tests do not establish a trusted production boundary.

## Security invariants

- Agent/world inputs and model outputs never authorize arbitrary host code execution. Any code-generation experiment is sandboxed with narrow capabilities, resource limits, and explicit operator policy.
- Credentials, host paths, environment variables, private external data, and unrelated network services are not exposed through agent observations, model context, memory, logs, or Minecraft communication.
- Every native action is authenticated to an agent/session, schema-validated, capability-checked, rate/timing bounded, and resolved by ordinary Minecraft mechanics and server policy. Malformed or unavailable actions fail closed.
- Partial-observability rules prevent hidden chunks, unseen entities, privileged server state, or another agent's private state from entering a baseline policy input.
- Per-agent identities, memories, relationships, caches, goals, and personal adapters remain isolated across storage, batching, logs, export, and deletion.
- Persistent writes are versioned and crash-safe; authorization precedes create/load/export/delete/migrate operations; failures cannot silently produce apparently valid state.
- Model, dataset, and checkpoint artifacts are verified by identity/checksum and compatibility before use; untrusted serialization formats are not deserialized with arbitrary-code capabilities.
- Human-facing systems disclose AI players where project/server policy requires it. The agent's internal ontology is never used to bypass human transparency.
- Server owners retain independently enforceable pause, disconnect, resource-limit, inspection, export, and deletion controls.
- Telemetry and training data enforce documented consent, access, retention, redaction, provenance, licensing, and deletion policy.

## Reportable findings and severity context

Report realistic violations of the invariants above, including host escape or code execution; credential/private-data exposure; unauthorized operator actions; world or inventory mutation outside legal mechanics; cross-agent identity or memory leakage; observation oracle leaks that invalidate claimed results; unsafe artifact loading; persistence corruption with integrity or authorization impact; denial of service across a server/agent population; or material consent/deletion failures.

Severity depends on reachability, required privileges, deployment exposure, affected agents/players/worlds, persistence, recoverability, and whether a control is enabled in the documented default. Host code execution, credential compromise, unauthorized administrative control, and broad cross-agent/private-player data exposure are normally high or critical. A research-result integrity flaw may also be high impact when it systematically creates false capability claims.

## Out of scope and limitations

The following are not security findings by themselves: poor gameplay skill; expected stochastic model errors that cannot cross a security boundary; balance disagreements on an explicitly experimental server; lack of protection from a fully authorized host administrator; or unsupported deployment configurations clearly documented as such. Bugs that turn these conditions into invariant violations remain reportable.

No network exposure, authentication model, deployment hardening, supported Minecraft version, or production security guarantee has yet been validated. Absence of implemented code is not evidence that future controls exist. New components must update this policy and the threat model as their boundaries become concrete.

## Safe research and disclosure

Test only systems and worlds you own or are authorized to assess. Minimize access to human data, use synthetic fixtures where possible, and coordinate disclosure before publishing exploit details. Security reports and fixes must not overstate whether broader research goals or consciousness claims have been established.
