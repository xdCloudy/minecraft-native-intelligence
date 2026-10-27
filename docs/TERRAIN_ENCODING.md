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

The reference run completed all 35 encoder/seed trials from clean commit
`0c0558f651acd2d2905a3658b11677fcfda8902e`: five seeds × seven representations,
with six terrain cases per trial. It ran on Windows 10 x64 with Python 3.11.9.
All 210 terrain cases passed hidden-state checks, including hidden-world
perturbation noninterference. The [run manifest](../experiments/terrain-encoding/results/geometry-local-encoding-v1_20261027T072802Z_53756ae112/run.json),
artifact hashes, logs, raw per-case metrics, and [summary](../experiments/terrain-encoding/results/geometry-local-encoding-v1_20261027T072802Z_53756ae112/summary.json)
are committed with this change.

Values below are medians across the 30 terrain cases per representation.
Payload and latency ranges show the 25th–75th percentiles of those case-level
measurements. Latencies are microseconds for encode plus JSON serialization,
and JSON parsing plus decode.

| Representation | Payload bytes, median (P25–P75) | Encode µs | Decode µs | Exact sample reconstruction | Nearest gold error, blocks | Local lookup / adjacency exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense | 38,758 (35,611–40,261) | 436 | 410 | 100% | 0.000 | 100% / 100% |
| Sparse | 18,726 (15,491–20,269) | 297 | 145 | 100% | 0.000 | 100% / 100% |
| Octree | 17,909 (14,716–18,833) | 654 | 263 | 100% | 0.000 | 100% / 100% |
| Graph | 20,706 (16,641–22,595) | 413 | 167 | 100% | 0.000 | 100% / 100% |
| Egocentric slices | 21,549 (17,987–24,461) | 469 | 216 | 100% | 0.000 | 100% / 100% |
| Chunk features | 4,981 (3,778–6,842) | 335 | 108 | 0% | 0.044 | 0% / 0% |
| Change events | 23,436 (17,836–26,672) | 639 | 290 | 100% | 0.000 | 100% / 100% |

Visible material counts were exact for all seven formats. The nearest-target
metric applied in 29 of 30 cases per format. Mean current/prior position
overlap was 0.201 (Jaccard) and the mean fraction of current samples repeated
from the prior view was 0.258.

### Recommendation

Use sparse visible samples as the initial lossless baseline for the next
prototype. In these fixtures it reconstructed every sample, supported all
tested spatial queries, and had lower median serialization latency than the
other lossless alternatives. Octrees reduced median payload size by about 4%
relative to sparse records, while taking about 2.2× as long to encode and 1.8×
as long to decode on this Python implementation. The graph representation
preserved explicit adjacency but cost about 11% more payload than sparse;
derive adjacency from sparse coordinates unless a later model or query workload
shows a benefit from storing edges.

Chunk features are a useful compact aggregate when only block counts matter.
They cannot reconstruct individual samples or answer the tested local and
adjacency queries. Change events were larger than sparse records at the measured
20% Jaccard overlap; high-overlap views were not tested, so this result does not
rule out event encoding for a different observation cadence.

### Limits

These measurements compare Python data structures on synthetic visible-surface
records, not real Minecraft worlds. They do not measure mod-side filtering,
client-equivalent occlusion, transport compression, model consumption, or agent
spatial reasoning. Timing is specific to the recorded Windows host and Python
version. The recommendation is a candidate for adapter-level testing, not a
production architecture decision or capability claim.

Summarize the committed raw run with:

```powershell
python scripts/summarize_terrain_encoding_run.py experiments/terrain-encoding/results/geometry-local-encoding-v1_20261027T072802Z_53756ae112
```
