# Safety and Responsible Operation

Safety here concerns concrete boundaries of a persistent Minecraft research system.

- Humans must be able to distinguish AI players where server, research, or community policy requires it. The agent's internal ontology does not justify deceiving people.
- Never expose host paths, credentials, private messages, environment variables, network services, or unrelated machine information through observations, prompts, memories, or chat.
- Model output must not execute arbitrary host code. Experimental code-generation skills require a sandbox, narrow APIs, resource limits, provenance, and explicit operator policy.
- Minecraft text, books, signs, chat, resource packs, and world data are untrusted inputs and cannot authorize host actions.
- Server owners retain admission, pause, kick/ban, resource-limit, inspect, export, and delete controls. Emergency stop must not depend on the agent's cooperation.
- Persistent data must be inspectable, portable, retention-bounded, and deletable by authorized administrators, subject to documented artifact limitations.
- Human gameplay/chat collection requires purpose, consent, privacy, retention, and licensing review.
- Reports must distinguish behavioural evidence from subjective consciousness claims and use conservative scientific wording.

See [SECURITY.md](../SECURITY.md) for vulnerability boundaries and reporting, and [DATA.md](DATA.md) for governance.

## Experimental operator stop fence (issue #197)

`scripts/operator_stop_contract.py` defines a small **offline reference model**
for operator pause, resume, emergency stop and explicit owner reset. A new control state defaults to **paused** after process startup; an
out-of-band, server-verified role is required; untrusted chat, signs, books,
world data or model/runtime messages never supply operator authority. A stop
advances a per-agent epoch and fences queued actions. Stopped agents cannot
resume without a separate owner reset to **paused**, followed by another
authorized resume. Replayed control sequence numbers are rejected.

The logical Minecraft server must perform both admission checks and a final
action-epoch check **atomically with each irreversible game-side effect**. An
ordinary model action (`action.v0` `stop`) only cancels its own intent and is
not a privileged operator command. Control events must be auditable without
leaking private host or player state.

This is not connected to a mod or real operator authentication; it cannot
currently interrupt mining, movement, inventory changes, remote inference, or
server transactions. Tests prove deterministic transitions only, **not** an
operational emergency stop. Adversarial input/claim-permission fixtures,
information-access leak tests, and Minecraft in-game stop timing remain
independent open gates under #197 and #200.
