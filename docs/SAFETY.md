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
