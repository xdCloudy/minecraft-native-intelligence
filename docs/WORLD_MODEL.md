# World Model

“World model” means learned or structured representations that predict relevant world dynamics and consequences; it does not commit to a particular neural architecture. A useful model may represent local geometry, object persistence, affordances, physics, other beings, needs, time, and uncertainty across multiple horizons.

Research should compare explicit simulators/graphs, latent predictive models, transformer-style sequence models, and hybrids. Predictions must be conditioned only on information legitimately observed by that agent. Uncertainty and stale knowledge are first-class: unloaded terrain or an absent player is not known merely because the server can inspect it.

Evaluate next-event prediction, multi-step rollout calibration, counterfactual action ranking, spatial permanence, changed-world detection, causal intervention, and downstream policy benefit. A lower prediction loss is insufficient if the representation leaks hidden state or fails to improve behaviour.
