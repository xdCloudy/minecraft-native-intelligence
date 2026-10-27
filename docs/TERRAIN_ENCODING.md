# Local terrain encoding comparison

Issue #6's first prototype is the reproducible synthetic benchmark in
`experiments/terrain-encoding/`. Its evaluation contract is
`docs/evaluation/terrain-encoding.v1.json`; the trial command is
`scripts/benchmark_terrain_encodings.py`.

## Compared representations

- **Dense voxels:** fixed 16³ local array. A null cell means unknown or
  unsampled, never air.
- **Sparse samples:** sorted records for visible samples only.
- **Octree:** sparse hierarchy with full visible sample data in leaves;
  missing branches mean unknown or unsampled.
- **Graph:** visible samples as nodes and geometric adjacency edges only
  between currently observed samples.
- **Egocentric slices:** visible samples grouped by local Y layer and Z row.
- **Chunk features:** lossy 4³ aggregates of visible sample counts, block
  histograms, and per-material centroids; never complete chunk contents.
- **Change events:** current/prior visible sample differences. A removal means
  a sample is no longer in the current observation collection, not that the
  block is absent from the world.

Each seed covers six deterministic synthetic patterns: open plane, cliff, cave
mouth, sparse cave, multi-level surface, and stepped ridge. Every policy input
uses partial coverage and `observed_items_only` negative evidence. The hidden
block map remains evaluator-only and is never passed to an encoder. A
noninterference check changes block identities outside both visible windows and
requires byte-identical output.

The benchmark reports compact JSON payload bytes, median encode-plus-serialize
and parse-plus-decode time,
exact visible-sample reconstruction, exact visible-material counts, nearest
visible gold distance error, lookup of an evaluator-selected visible sample,
visible adjacency
preservation, and hidden-state conformance. Timing uses seven in-process
measurements per terrain case; raw case results are retained in each trial's
`terrain-encoding.json` artifact. Current/prior visible-position overlap is
also recorded to interpret the change-event representation's bandwidth.

## Run

Use a clean checkout and Python 3.11 or newer:

```powershell
python scripts/run_experiment.py --manifest experiments/terrain-encoding/experiment.json
```

The deterministic boundary and reconstruction checks used by CI are:

```powershell
python scripts/benchmark_terrain_encodings.py --self-check
```

## Evidence limits

This benchmark is a data-structure comparison on synthetic visible-surface
records. It does not launch Minecraft, validate client-equivalent occlusion,
measure network transport, run a spatially reasoning agent, or compare learned
policies. Latency numbers describe this Python prototype on the recorded
machine only. They can narrow representation candidates, but production choice
requires adapter integration and Minecraft conformance tests.

## Results

No result table is published until the experiment has completed from a clean,
committed revision. The run manifest and raw per-trial artifacts are the source
for any subsequent recommendation.
