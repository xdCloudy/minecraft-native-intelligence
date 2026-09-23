# Java and research-runtime process boundary

Status: architecture recommendation for issue #2, researched 2026-09-22.

## Decision summary

Use an **asynchronous out-of-process runtime** as the default boundary between
the Minecraft Java mod and the research/model runtime.

Use **gRPC with binary Protocol Buffers over a local loopback connection** as
the first portable transport baseline. The Minecraft mod owns the client side of
the runtime protocol; the runtime service owns cognition, memory orchestration,
model access, batching, and research-specific dependencies.

Keep a narrow **in-process Java runtime SPI** for deterministic test doubles,
embodiment spikes, and deliberately simple research baselines. It must implement
the same semantic contracts and must not become a second architecture.

Do not make shared memory, JNI, embedded Python, or a particular model runtime a
baseline dependency. Shared-memory bulk transfer may be added behind the same
protocol boundary only if profiling proves serialization/copying is a material
bottleneck.

The Minecraft logical server must never synchronously wait for model inference
on its tick thread. Runtime latency changes cognition freshness, not Minecraft
server availability.

## Why this boundary fits the project

The project already separates:

- server-authoritative Minecraft integration;
- versioned observation, event, action, and outcome contracts;
- per-agent persistent state;
- a shared model/runtime layer; and
- later model, memory, training, and evaluation experimentation.

An out-of-process service preserves those seams while allowing the research side
to use Java, Python, native GPU libraries, or another stack without embedding
their dependency and failure model into the Minecraft JVM.

This decision is about the process boundary and transport contract. It does not
select a model family, inference engine, training framework, database, or
research language.

## Non-negotiable invariants

The process boundary must preserve these invariants:

1. Minecraft remains authoritative for world state and legal actions.
2. No model/runtime failure may stall the Minecraft server tick indefinitely.
3. Runtime messages are explicitly associated with one agent identity and one
   runtime session.
4. Cross-agent batching must not collapse private state ownership.
5. Stale, duplicate, malformed, unauthorized, or incompatible actions fail
   closed.
6. A disconnected runtime cannot cause a fallback chatbot, hidden-state oracle,
   direct world mutation, or arbitrary host execution.
7. Runtime replacement or restart must not silently create a new agent identity.
8. The protocol contains Minecraft-native domain data, not Fabric, gRPC, model,
   tensor-library, or Python-specific application semantics.
9. Protocol evolution is explicit and testable.
10. The default deployment is local-only unless a separate security decision
    approves remote exposure.

## Boundary candidates

| Criterion | In-process Java SPI | Local gRPC + Protobuf service | Shared-memory bulk path |
| --- | --- | --- | --- |
| Baseline role | Test double / simple baseline | **Default research runtime** | Deferred optimization |
| Language freedom | Low | High | Medium; bindings/platform work required |
| Failure isolation | Poor: runtime crash/OOM/native failure can affect Minecraft JVM | Stronger: runtime process can fail/restart independently | Medium; process isolation exists but corrupt/shared state handling is harder |
| Server-tick safety | Good only if all calls are explicitly asynchronous | Good with async streaming and bounded queues | Good only with careful non-blocking synchronization |
| Serialization overhead | Minimal | Present; benchmark required | Lowest bulk-copy potential |
| Schema/version discipline | Easy to accidentally bypass with Java object references | Strong: explicit wire schema | Must still define schema/layout/versioning |
| Multi-agent batching | Possible | Natural through stream/batch envelopes | Possible but coordination is more complex |
| Health/recovery | Custom | Standard health checks plus reconnect logic | Custom |
| Debug/replay | Simple inside one JVM, but coupled | Strong if messages/traces are captured as fixtures | Harder to inspect safely |
| Deployment | One JVM | Additional local service/process | Additional process plus platform-specific shared-memory plumbing |
| Windows/Linux portability | Strong | Strong with loopback TCP | Requires platform-specific implementation details |
| Dependency isolation | Poor | Strong | Stronger than in-process, but native plumbing grows |
| Security surface | Small process surface, large shared privilege | Explicit local IPC boundary that can be authenticated | Shared-memory permissions and lifecycle add complexity |
| Recovery from model/native crash | Usually Minecraft JVM restart | Runtime restart and protocol resynchronization | Runtime restart plus shared-region reinitialization |
| Recommended now | No, except test/simple runtime | **Yes** | No, profile first |

## Costed comparison

### In-process Java SPI

Benefits:

- essentially no transport/serialization cost;
- easiest path for deterministic fake runtimes and unit tests;
- convenient during the earliest player-embodiment spike;
- one process to launch and debug.

Costs and risks:

- model/native library crashes, leaks, OOMs, long GC pauses, or dependency
  conflicts can affect the Minecraft JVM;
- strongly biases research toward JVM-compatible tooling;
- couples Minecraft lifecycle to model/runtime lifecycle;
- makes independent runtime restart and upgrade difficult;
- makes it easier for code to bypass versioned domain contracts and pass
  implementation objects directly;
- GPU frameworks and Python-first research code require JNI, embedded Python, or
  equivalent complexity if they must live in-process.

Conclusion: retain only as a narrow interface implementation for tests and
simple baselines. Do not make it the primary learned-runtime architecture.

### Local gRPC with binary Protocol Buffers

Benefits:

- first-class Java and Python support plus other research languages;
- generated typed clients/servers from one language-neutral schema;
- bidirectional streaming supports independent asynchronous observation and
  action flow while preserving order within each stream;
- deadlines prevent unbounded waits for request-style operations;
- a standard health service exists for runtime readiness;
- process failure and native/GPU dependency failures are isolated from the game
  JVM;
- a runtime can restart, reject work, or scale its own batching without changing
  Minecraft-facing semantics;
- Protocol Buffers provide explicit binary schema evolution rules and preserve
  unknown fields across binary parsing/serialization.

Costs and risks:

- another process must be installed, started, monitored, and upgraded;
- serialization and loopback transport add latency and CPU cost;
- HTTP/2/gRPC libraries increase the mod/runtime dependency surface;
- connection loss, backpressure, retries, duplicate messages, and protocol
  negotiation require explicit design;
- a carelessly exposed listener would create an unnecessary network/control
  boundary.

Conclusion: best default balance of replaceability, isolation, language
independence, debugging, and mature protocol behavior. Performance must be
validated rather than assumed.

### Shared memory

Benefits:

- can avoid repeated copies for large dense payloads;
- potentially useful for high-rate observations or tensor-like bulk features.

Costs and risks:

- cross-platform lifecycle, permissions, cleanup, crash recovery, and
  synchronization are substantially more complex;
- corruption or producer/consumer disagreement can be harder to contain and
  debug;
- layout/version changes become another compatibility system;
- small structured control messages gain little from the complexity;
- premature adoption would couple observation representation to transport
  optimization before real profiles exist.

Conclusion: do not adopt for the baseline. If profiling later shows that gRPC
serialization/copying consumes a material share of latency or CPU, add an
optional versioned shared-memory payload channel while retaining gRPC as the
control/health/negotiation plane.

## Transport baseline

The initial transport is a localhost-only gRPC endpoint using binary Protocol
Buffers.

Use loopback TCP as the portable baseline because the project targets both
Windows and Linux/headless deployments. Platform-specific local transports such
as Unix domain sockets may be benchmarked later, but must not create different
protocol semantics.

The listener must bind only to loopback by default. Remote listening is out of
scope for this issue and requires explicit authentication, encryption,
authorization, deployment, and threat-model work.

## Protocol shape

Use one long-lived asynchronous runtime session rather than a synchronous RPC
per Minecraft tick.

Conceptually, the protocol contains:

### Session negotiation

- protocol major/minor version;
- implementation identity/version;
- Minecraft/mod/environment schema versions;
- supported capabilities;
- compression capabilities if introduced;
- maximum accepted message/batch sizes;
- runtime readiness;
- session epoch/nonce; and
- optional authentication material supplied by the local service-management
  layer.

An incompatible major version fails closed before actions are accepted.

### Observation/event envelopes

Every envelope carries at least:

- agent ID;
- runtime session epoch;
- monotonically increasing per-agent sequence;
- Minecraft game/tick time;
- observation schema version;
- trace/correlation ID;
- observation snapshot or versioned delta/event batch;
- validity/visibility metadata defined by the native interface; and
- optional producer timestamp for diagnostics, never as an authority over game
  time.

### Action envelopes

Every requested action carries:

- agent ID;
- runtime session epoch;
- action request ID;
- the observation/event sequence or state revision it was derived from;
- action schema version;
- requested action/intention;
- validity/deadline semantics where relevant; and
- trace/correlation ID.

Minecraft's legal-action validator remains final authority. The transport never
grants capability by itself.

### Action outcomes

Accepted, rejected, cancelled, started, and completed outcomes are returned as
ordinary versioned environment events. The runtime must not infer success merely
because an action was sent.

### Control messages

Keep a small explicit control surface for:

- runtime/session readiness;
- agent attach/detach/pause/resume;
- resynchronization request;
- capability updates;
- backpressure/degradation signal;
- graceful shutdown; and
- diagnostic/health state.

Administrative Minecraft lifecycle authorization remains in the mod/operator
boundary rather than being delegated to the model.

## Tick and latency model

Minecraft uses logical ticks at 20 ticks per second under normal timing, so one
tick represents roughly 50 ms. This is the server's entire simulation cadence,
not an IPC budget.

Therefore:

- never execute a blocking model call on the logical-server tick thread;
- never require an action response for every tick;
- capture/publish bounded state asynchronously;
- allow low-level action intentions to remain active across multiple ticks when
  the action contract permits it;
- treat reactive, behavioural, deliberative, consolidation, and learning loops
  as different cadences;
- discard or reject stale decisions according to explicit action validity
  rules; and
- degrade cognition or pause an agent rather than stalling the world.

### Initial transport performance gate

Before the boundary is considered production-worthy, benchmark the protocol
without model inference and report p50/p95/p99.

The first engineering target is:

- p99 local transport + encode/decode latency at or below **5 ms** for the
  representative structured-control payload sizes selected by the observation
  schema work;
- no synchronous Minecraft tick wait on that round trip;
- bounded memory under backpressure; and
- no cross-agent ordering or state-isolation failure under load.

The 5 ms number is an engineering guardrail, not a measured capability claim. It
reserves most of a normal 50 ms tick for Minecraft and other integration work.
If the real workload needs a different threshold, change the target through
measured evidence and an ADR update.

Do not define an inference-latency SLO yet. Model family, hardware, cognition
cadence, batching, and observation encoding are unresolved and must be measured
separately.

## Throughput benchmark plan

Benchmark at least:

- 1, 16, 64, and 128 logical agents;
- representative small/medium/large observation payloads produced by the actual
  schema prototypes;
- 1, 5, 10, and 20 observation publications per second where semantically
  meaningful;
- individual and batched envelopes;
- idle/distant versus active agent mixes;
- runtime consuming normally, consuming slowly, disconnected, and reconnecting;
- Windows and Linux where supported;
- Java client with at least one non-JVM reference runtime, preferably Python
  because it is a likely research environment but not an architectural
  requirement.

Measure:

- encode/decode latency;
- one-way and round-trip transport latency;
- throughput and bytes/sec;
- Minecraft-side CPU;
- runtime-side CPU;
- allocation/GC pressure;
- memory/queue growth;
- dropped/coalesced messages;
- p50/p95/p99 end-to-end protocol latency;
- reconnect/resynchronization time; and
- cross-agent ordering/isolation violations.

Record exact hardware, OS, JVM, runtime, gRPC, Protobuf, message schema, payload
sizes, compression, batch sizes, and commands.

## Backpressure and queue policy

All queues are bounded.

Do not accumulate an unbounded history of snapshots while a runtime is slow.

Different message classes need different handling:

- **replaceable state snapshots:** a newer complete snapshot may supersede an
  older unsent snapshot;
- **ordered world/action events:** do not silently coalesce events whose loss
  changes semantics; preserve them or force an explicit resynchronization;
- **action outcomes:** preserve ordering and correlation until acknowledged or
  the session is invalidated;
- **diagnostics:** may use independently bounded sampling/drop policies.

If a required ordered stream falls behind its configured bound, mark the
runtime/agent degraded and require resynchronization rather than guessing over a
sequence gap.

## Failure and recovery behavior

### Runtime unavailable at startup

The Minecraft mod loads independently. Runtime-backed agents cannot begin
cognition and surface a clear operator state. Existing persistent identities
remain recoverable.

### Runtime crashes or disconnects

- Minecraft keeps running.
- No new runtime-generated actions are accepted from the dead session.
- Active actions are cancelled or allowed to reach a safe defined boundary
  according to the action contract.
- The AI entity enters the configured safe paused/idle state.
- The mod records the failure and runtime session epoch.
- Reconnection requires a fresh handshake and state resynchronization before new
  actions are accepted.

### Runtime hangs

Health checks alone are insufficient. Bounded queues, application-level progress
signals, and deadlines on request-style RPCs prevent an apparently connected but
non-responsive runtime from consuming unbounded resources.

### Duplicate/replayed messages

Session epoch + per-agent sequence + action request IDs make duplicates
detectable. A request from an old session epoch is rejected.

### Schema mismatch

Incompatible major protocol/schema versions fail closed with an operator-visible
error. Additive compatible fields negotiate normally.

### Minecraft server stopping

Stop accepting new runtime actions, flush only bounded required lifecycle state,
signal graceful shutdown/detach, and never let runtime shutdown block the server
indefinitely.

## Versioning policy

Use binary Protocol Buffers on the wire.

Protocol evolution rules:

- never reuse a field number;
- reserve removed field numbers and names;
- prefer additive optional fields;
- preserve unknown fields through binary parsing/serialization;
- do not use ProtoJSON as the canonical runtime wire format because conversion
  can lose unknown fields and has different compatibility constraints;
- version semantic contracts explicitly even when a wire change is technically
  parseable;
- keep protocol major/minor negotiation separate from Minecraft game version,
  observation schema version, action schema version, and persistent-store
  version;
- maintain golden compatibility fixtures for the oldest supported adjacent
  versions; and
- make incompatible migrations deliberate rather than hidden in generated-code
  upgrades.

Pin gRPC, Protobuf compiler/runtime, and code-generation plugin versions when
implementation begins. Do not use floating latest dependencies.

## Security boundary

The local runtime is not automatically trusted just because it runs on the same
machine.

Baseline controls:

- loopback-only listener;
- connection/session authentication supplied by the later service-management
  layer;
- no arbitrary remote bind in default configuration;
- maximum message sizes;
- bounded queues and rate limits;
- schema validation;
- per-agent authorization/isolation;
- no host paths, credentials, environment variables, or unrelated files in
  protocol messages;
- no runtime request can bypass Minecraft's legal-action validator;
- privacy-aware trace/log redaction; and
- explicit opt-in/security review before remote runtime transport.

The detailed distributable service discovery/authentication and crash-management
implementation remains later work; this issue defines the boundary it must
protect.

## Debugging and observability

Every cross-boundary message should be traceable without requiring packet
inspection.

Record:

- trace/correlation ID;
- agent ID in a privacy-safe internal form;
- session epoch;
- sequence/request ID;
- schema/protocol versions;
- enqueue/send/receive/validate/outcome timestamps;
- payload size, not raw private payload by default;
- queue depth/backpressure state;
- result/rejection code; and
- runtime health transitions.

Provide a fixture/replay representation that can reproduce protocol state
without requiring a live model. Raw human data follows the data-governance
policy and must not be copied into debug bundles by default.

## In-process SPI rules

The in-process implementation exists to speed testing, not to weaken the
architecture.

It must:

- consume the same logical observation/event contracts;
- emit the same logical action requests;
- obey asynchronous scheduling;
- preserve per-agent identities and session semantics;
- pass the same contract tests;
- never expose Minecraft implementation objects directly to policy code; and
- be replaceable by the out-of-process implementation without changing
  Minecraft-facing behavior.

A deterministic no-op/scripted test runtime must be clearly labelled as
scaffolding and is not evidence of learned intelligence.

## Falsifiers and reconsideration triggers

Reconsider gRPC/Protobuf as the baseline if a reproducible benchmark shows any
of the following after straightforward tuning:

- local transport/serialization consumes a material share of the Minecraft tick
  or runtime CPU budget at the required agent population;
- p99 protocol overhead materially exceeds the declared transport gate for
  representative payloads;
- backpressure cannot be bounded without losing required event semantics;
- Java plus the selected research language cannot interoperate reliably across
  supported Windows/Linux environments;
- dependency size/conflicts materially compromise the Minecraft mod; or
- a simpler versioned transport provides equal language support, recovery,
  debugging, and schema discipline with materially lower cost.

If only large payload copying is the bottleneck, prefer adding an optional
shared-memory data plane rather than replacing the control protocol wholesale.

## Implementation sequence

1. Define the language-neutral protocol package and lifecycle state machine.
2. Implement an in-process deterministic runtime adapter for contract tests.
3. Implement the Java async gRPC client in the mod-side integration layer.
4. Implement one minimal reference runtime service outside the Minecraft JVM.
5. Add health, handshake, bounded queues, sequence/session validation, and
   resynchronization.
6. Add deterministic protocol contract tests and fault injection.
7. Run the benchmark matrix locally.
8. Record results and tune message/batch sizes.
9. Only then attach a real model runtime.
10. Keep remote exposure disabled unless separate security/runtime-service work
    explicitly enables it.

## Primary sources

- [gRPC documentation](https://grpc.io/docs/)
- [gRPC Java basics](https://grpc.io/docs/languages/java/basics/)
- [gRPC deadlines](https://grpc.io/docs/guides/deadlines/)
- [gRPC health checking](https://grpc.io/docs/guides/health-checking/)
- [Protocol Buffers proto3 guide](https://protobuf.dev/programming-guides/proto3/)
- [Protocol Buffers Editions guide](https://protobuf.dev/programming-guides/editions/)
- [Fabric logical-tick example](https://docs.fabricmc.net/develop/items/custom-fuel)

## Follow-up implications

This decision unblocks:

- runtime scheduler design;
- evaluation/experiment runner process integration;
- later model-serving selection;
- runtime service management/discovery/authentication;
- observability and tracing; and
- native Minecraft integration using deterministic runtime stubs before a real
  model exists.

The later implementation should validate this transport against measured
Minecraft-side and many-agent workloads rather than treating the design
document as a benchmark result.
