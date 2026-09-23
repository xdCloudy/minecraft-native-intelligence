# Native Perception

The interface should expose structured observations and events derived from Minecraft mechanics: bounded local blocks/geometry, visible or otherwise legitimately sensed entities, inventory and equipment, health/hunger/status, pose and velocity, time/weather, sounds, chat, interaction outcomes, and object/crafting properties the agent has legitimately acquired.

Each field needs coordinate frame, units, validity/visibility mask, sampling/event semantics, version, channel, policy-visibility flag, and one or more access-rule IDs from [INFORMATION_ACCESS.md](INFORMATION_ACCESS.md). Field-of-view, occlusion, distance, sound delivery, chunk/client availability, darkness/fog, ownership, recipient rules, and server configuration determine access. Loaded or simulated server state does not grant perception. The design must separate current interface facts, protocol/evaluator metadata, and remembered/inferred state so learned beliefs are not presented as observations.

The baseline uses **access equivalence rather than pixel equivalence**: once a fact is legitimately available through the player's senses or ordinary non-debug UI, it may be encoded structurally without requiring a vision/audio classifier. Unseen/occluded/unavailable facts remain unknown even when the server can inspect them. The machine-readable baseline rules and conformance cases live in `docs/information_access/`.

Open questions include voxel/token/graph representations, temporal event encoding, observation bandwidth, Minecraft-version stability, precision quantization, and exact server-side approximation of client visual effects. Screenshot perception may be retained only as an explicitly labelled comparison experiment.
