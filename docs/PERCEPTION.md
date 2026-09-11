# Native Perception

The interface should expose structured observations and events derived from Minecraft mechanics: bounded local blocks/geometry, visible or otherwise legitimately sensed entities, inventory and equipment, health/hunger/status, pose and velocity, time/weather, sounds, chat, interaction outcomes, and object/crafting properties the agent has legitimately acquired.

Each field needs coordinate frame, units, validity/visibility mask, sampling/event semantics, and version. Field-of-view, occlusion, distance, sound propagation, chunk loading, darkness, and server rules determine access. The design must separate raw interface facts from inferred state so learned beliefs are not presented as observations.

Open questions include voxel/token/graph representations, temporal event encoding, observation bandwidth, Minecraft-version stability, and the balance between ordinary-player equivalence and accessible structured state. Screenshot perception may be retained only as an explicitly labelled comparison experiment.
