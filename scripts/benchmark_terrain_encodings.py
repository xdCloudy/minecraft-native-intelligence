#!/usr/bin/env python3
"""Benchmark lossless and lossy local-geometry prototypes on synthetic views.

This is a representation experiment only. Encoders receive a bounded policy
observation and, for change events, a prior policy observation. Evaluator-only
world truth never enters an encoder call.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
TRIAL_DIR = Path(os.environ.get("MNI_TRIAL_DIR", ROOT / ".terrain-benchmark"))
SEED = int(os.environ.get("MNI_SEED", "101"))
VARIANT = os.environ.get("MNI_ENCODER", "sparse")
ENCODERS = ("dense", "sparse", "octree", "graph", "egocentric_slices", "chunk_features", "change_events")
TERRAINS = ("open_plane", "cliff", "cave_mouth", "sparse_cave", "multi_level", "stepped_ridge")
MIN = -8
SIZE = 16
BLOCKS = (
    "minecraft:stone",
    "minecraft:grass_block",
    "minecraft:deepslate",
    "minecraft:oak_planks",
    "minecraft:gold_block",
    "minecraft:water",
)
SAMPLE_KEYS = {"sample_id", "relative_block", "block_id", "visible_properties", "visible_faces", "fluid_id", "visibility_quality"}


def pos_key(sample: dict[str, Any]) -> tuple[int, int, int]:
    p = sample["relative_block"]
    return p["x"], p["y"], p["z"]


def sample_sort_key(sample: dict[str, Any]) -> tuple[int, int, int, str]:
    return (*pos_key(sample), sample["block_id"])


def make_world(terrain: str, seed: int) -> dict[tuple[int, int, int], str]:
    rng = random.Random(seed)
    world: dict[tuple[int, int, int], str] = {}
    xs = range(MIN, MIN + SIZE)
    ys = range(MIN, MIN + SIZE)
    zs = range(MIN, MIN + SIZE)

    if terrain == "open_plane":
        coordinates = [(x, 0, z) for x in xs for z in zs]
    elif terrain == "cliff":
        coordinates = [(4, y, z) for y in range(-7, 8) for z in zs]
    elif terrain == "cave_mouth":
        coordinates = [(3, y, z) for y in range(-7, 8) for z in range(-7, 8)]
        coordinates = [p for p in coordinates if not (-2 <= p[1] <= 2 and -2 <= p[2] <= 2)]
        coordinates += [(x, -4, z) for x in range(4, 8) for z in range(-7, 8)]
    elif terrain == "sparse_cave":
        coordinates = [(x, y, z) for x in range(-7, 8) for y in range(-4, 5) for z in range(-7, 8)
                       if (x * x + y * y + z * z) % 11 < 3]
    elif terrain == "multi_level":
        coordinates = [(x, y, z) for x in xs for z in zs for y in (-4, 0, 4)
                       if rng.random() < 0.28]
    elif terrain == "stepped_ridge":
        coordinates = [(x, max(-6, min(6, (x // 3) + (z // 4))), z) for x in xs for z in zs]
    else:
        raise ValueError(f"unknown terrain: {terrain}")

    for p in sorted(set(coordinates)):
        material = rng.choices(BLOCKS, weights=(34, 24, 17, 10, 4, 11), k=1)[0]
        world[p] = material
    return world


def visible_positions(world: dict[tuple[int, int, int], str], terrain: str, seed: int, view: int) -> set[tuple[int, int, int]]:
    rng = random.Random(seed * 31 + view * 1009)
    result = set()
    for p in world:
        x, y, z = p
        if terrain == "open_plane":
            visible = (z >= 0 if view == 0 else z <= 0) and rng.random() < 0.82
        elif terrain == "cliff":
            visible = (z >= 0 if view == 0 else z <= 0) and rng.random() < 0.9
        elif terrain == "cave_mouth":
            visible = p[0] == 3 and rng.random() < 0.95
        elif terrain == "sparse_cave":
            visible = rng.random() < (0.18 if view == 0 else 0.2)
        elif terrain == "multi_level":
            visible = (x >= 0 if view == 0 else x <= 0) and rng.random() < 0.62
        else:
            visible = (x + z >= 0 if view == 0 else x + z <= 0) and rng.random() < 0.7
        if visible:
            result.add(p)
    return result


def make_observation(world: dict[tuple[int, int, int], str], visible: set[tuple[int, int, int]], sequence: int) -> dict[str, Any]:
    items = []
    for i, p in enumerate(sorted(visible)):
        block_id = world[p]
        face = "north" if block_id != "minecraft:water" and p[1] != 0 else "up"
        items.append({
            "sample_id": f"s{i}",
            "relative_block": {"x": p[0], "y": p[1], "z": p[2]},
            "block_id": block_id,
            "visible_properties": {},
            "visible_faces": [face],
            "fluid_id": "minecraft:water" if block_id == "minecraft:water" else None,
            "visibility_quality": 1.0,
        })
    return {
        "sequence": sequence,
        "coverage": {"status": "partial", "negative_evidence": "observed_items_only", "reason_codes": ["outside_frustum", "occlusion"]},
        "scope": {"origin": MIN, "size": SIZE, "frame": "agent_local"},
        "items": items,
    }


def encode_sparse(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    return {"kind": "sparse", "coverage": observation["coverage"], "scope": observation["scope"],
            "items": sorted(observation["items"], key=sample_sort_key)}


def encode_dense(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    cells: list[dict[str, Any] | None] = [None] * (SIZE ** 3)
    for sample in observation["items"]:
        x, y, z = pos_key(sample)
        index = ((y - MIN) * SIZE + (z - MIN)) * SIZE + (x - MIN)
        cells[index] = sample
    return {"kind": "dense", "coverage": observation["coverage"], "scope": observation["scope"],
            "dimensions": [SIZE, SIZE, SIZE], "cells": cells, "null_semantics": "unknown_or_not_sampled"}


def encode_octree(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    def build(items: list[dict[str, Any]], origin: tuple[int, int, int], size: int) -> Any:
        if not items:
            return None
        if size == 1:
            if len(items) != 1:
                raise ValueError("multiple samples occupy one voxel")
            sample = dict(items[0])
            sample.pop("relative_block")
            return {"sample": sample}
        half = size // 2
        buckets: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for sample in items:
            x, y, z = pos_key(sample)
            child = int(x >= origin[0] + half) | (int(y >= origin[1] + half) << 1) | (int(z >= origin[2] + half) << 2)
            buckets[child].append(sample)
        children = {}
        for child, members in sorted(buckets.items()):
            child_origin = (origin[0] + (half if child & 1 else 0),
                            origin[1] + (half if child & 2 else 0),
                            origin[2] + (half if child & 4 else 0))
            children[str(child)] = build(members, child_origin, half)
        return {"children": children}
    return {"kind": "octree", "coverage": observation["coverage"], "scope": observation["scope"],
            "root": build(observation["items"], (MIN, MIN, MIN), SIZE),
            "missing_child_semantics": "unknown_or_not_sampled"}


def encode_graph(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    items = sorted(observation["items"], key=sample_sort_key)
    lookup = {pos_key(item): item["sample_id"] for item in items}
    edges = []
    for item in items:
        x, y, z = pos_key(item)
        for neighbor in ((x + 1, y, z), (x, y + 1, z), (x, y, z + 1)):
            if neighbor in lookup:
                edges.append([item["sample_id"], lookup[neighbor]])
    return {"kind": "graph", "coverage": observation["coverage"], "scope": observation["scope"],
            "nodes": items, "adjacent_visible_sample_edges": edges,
            "edge_semantics": "geometric adjacency among observed samples only"}


def encode_slices(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    layers: dict[int, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for sample in observation["items"]:
        x, y, z = pos_key(sample)
        layers[y][z].append({"x": x, "sample": sample})
    encoded_layers = []
    for y in sorted(layers):
        rows = []
        for z in sorted(layers[y]):
            rows.append({"z": z, "items": sorted(layers[y][z], key=lambda item: item["x"])})
        encoded_layers.append({"y": y, "rows": rows})
    return {"kind": "egocentric_slices", "coverage": observation["coverage"], "scope": observation["scope"],
            "layers": encoded_layers, "missing_slice_semantics": "unknown_or_not_sampled"}


def encode_chunks(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    chunks: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for sample in observation["items"]:
        p = pos_key(sample)
        key = tuple((coordinate - MIN) // 4 for coordinate in p)
        chunks[key].append(sample)
    encoded = []
    for key in sorted(chunks):
        samples = chunks[key]
        by_block: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
        for sample in samples:
            by_block[sample["block_id"]].append(pos_key(sample))
        encoded.append({
            "chunk": list(key),
            "visible_sample_count": len(samples),
            "visible_block_histogram": {block: len(coords) for block, coords in sorted(by_block.items())},
            "visible_position_centroid_by_block": {
                block: [sum(p[i] for p in coords) / len(coords) for i in range(3)]
                for block, coords in sorted(by_block.items())
            },
        })
    return {"kind": "chunk_features", "coverage": observation["coverage"], "scope": observation["scope"],
            "chunks": encoded, "semantics": "aggregates of observed samples only; not complete chunk contents"}


def encode_changes(observation: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    if previous is None:
        raise ValueError("change-event encoding requires a prior policy observation")
    before = {pos_key(item): item for item in previous["items"]}
    after = {pos_key(item): item for item in observation["items"]}
    events = []
    for p in sorted(set(before) | set(after)):
        old, current = before.get(p), after.get(p)
        if old is None:
            events.append({"op": "upsert", "item": current})
        elif current is None:
            events.append({"op": "no_longer_in_current_collection", "position": list(p)})
        elif old["block_id"] != current["block_id"] or {k: v for k, v in old.items() if k != "sample_id"} != {k: v for k, v in current.items() if k != "sample_id"}:
            events.append({"op": "upsert", "item": current})
        else:
            events.append({"op": "reobserved", "position": list(p), "sample_id": current["sample_id"]})
    return {"kind": "change_events", "coverage": observation["coverage"], "scope": observation["scope"],
            "base_sequence": previous["sequence"], "current_sequence": observation["sequence"],
            "events": events,
            "remove_semantics": "remove_from_current_observation_view_only_not_world_absence"}


ENCODE: dict[str, Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any]]] = {
    "dense": encode_dense,
    "sparse": encode_sparse,
    "octree": encode_octree,
    "graph": encode_graph,
    "egocentric_slices": encode_slices,
    "chunk_features": encode_chunks,
    "change_events": encode_changes,
}


def decode(encoded: dict[str, Any], previous: dict[str, Any] | None) -> list[dict[str, Any]]:
    kind = encoded["kind"]
    if kind == "sparse":
        return encoded["items"]
    if kind == "dense":
        result = []
        for index, sample in enumerate(encoded["cells"]):
            if sample is None:
                continue
            x = index % SIZE + MIN
            z = (index // SIZE) % SIZE + MIN
            y = index // (SIZE * SIZE) + MIN
            result.append(sample)
            if pos_key(sample) != (x, y, z):
                raise ValueError("dense coordinate/index mismatch")
        return result
    if kind == "octree":
        result = []
        def visit(node: Any, origin: tuple[int, int, int], size: int) -> None:
            if node is None:
                return
            if "sample" in node:
                sample = dict(node["sample"])
                sample["relative_block"] = {"x": origin[0], "y": origin[1], "z": origin[2]}
                result.append(sample)
                return
            half = size // 2
            for child_text, child_node in node["children"].items():
                child = int(child_text)
                child_origin = (origin[0] + (half if child & 1 else 0),
                                origin[1] + (half if child & 2 else 0),
                                origin[2] + (half if child & 4 else 0))
                visit(child_node, child_origin, half)
        visit(encoded["root"], (MIN, MIN, MIN), SIZE)
        return result
    if kind == "graph":
        return encoded["nodes"]
    if kind == "egocentric_slices":
        return [entry["sample"] for layer in encoded["layers"] for row in layer["rows"] for entry in row["items"]]
    if kind == "chunk_features":
        result = []
        for chunk in encoded["chunks"]:
            for block, count in chunk["visible_block_histogram"].items():
                result.append({
                    "sample_id": f"aggregate-{chunk['chunk'][0]}-{chunk['chunk'][1]}-{chunk['chunk'][2]}-{block}",
                    "relative_block": dict(zip(("x", "y", "z"), chunk["visible_position_centroid_by_block"][block])),
                    "block_id": block,
                    "visible_properties": {},
                    "visible_faces": [],
                    "fluid_id": None,
                    "visibility_quality": None,
                    "source_count": count,
                })
        return result
    if kind == "change_events":
        if previous is None or encoded["base_sequence"] != previous["sequence"]:
            raise ValueError("change-event base sequence mismatch")
        current = {pos_key(item): item for item in previous["items"]}
        for event in encoded["events"]:
            if event["op"] == "no_longer_in_current_collection":
                current.pop(tuple(event["position"]), None)
            elif event["op"] == "upsert":
                item = event["item"]
                current[pos_key(item)] = item
            elif event["op"] == "reobserved":
                p = tuple(event["position"])
                if p not in current:
                    raise ValueError("reobserved event lacks a prior visible sample")
                current[p] = {**current[p], "sample_id": event["sample_id"]}
            else:
                raise ValueError(f"unknown change event {event['op']!r}")
        return list(current.values())
    raise ValueError(f"unknown encoder {kind!r}")


def validate_policy_input(observation: dict[str, Any]) -> None:
    if set(observation) != {"sequence", "coverage", "scope", "items"}:
        raise ValueError("encoder input contains fields outside the bounded policy observation")
    if set(observation["coverage"]) != {"status", "negative_evidence", "reason_codes"}:
        raise ValueError("coverage has unexpected fields")
    if observation["coverage"]["negative_evidence"] != "observed_items_only":
        raise ValueError("partial fixture must not assert unobserved absence")
    for sample in observation["items"]:
        if set(sample) != SAMPLE_KEYS:
            raise ValueError("sample contains fields outside the v0 visible-surface contract")


def exact_key(sample: dict[str, Any]) -> tuple[Any, ...]:
    return (sample["sample_id"], *pos_key(sample), sample["block_id"],
            json.dumps(sample["visible_properties"], sort_keys=True), tuple(sample["visible_faces"]),
            sample["fluid_id"], sample["visibility_quality"])


def histogram(samples: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(sample["block_id"] for sample in samples).items()))


def chunk_histogram(encoded: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for chunk in encoded["chunks"]:
        counts.update(chunk["visible_block_histogram"])
    return dict(sorted(counts.items()))


def nearest_gold(samples: list[dict[str, Any]]) -> float | None:
    distances = [math.sqrt(sum(c * c for c in pos_key(sample))) for sample in samples if sample["block_id"] == "minecraft:gold_block"]
    return min(distances) if distances else None


def chunk_nearest_gold(encoded: dict[str, Any]) -> float | None:
    points = []
    for chunk in encoded["chunks"]:
        if chunk["visible_block_histogram"].get("minecraft:gold_block", 0):
            p = chunk["visible_position_centroid_by_block"]["minecraft:gold_block"]
            points.append(math.sqrt(sum(c * c for c in p)))
    return min(points) if points else None


def local_block(samples: list[dict[str, Any]], position: tuple[int, int, int] = (0, 0, 0)) -> str | None:
    return next((sample["block_id"] for sample in samples
                 if pos_key(sample) == position and sample.get("source_count", 1) == 1), None)


def visible_adjacencies(samples: list[dict[str, Any]]) -> list[tuple[str, str]]:
    lookup = {pos_key(sample): sample["sample_id"] for sample in samples}
    edges = []
    for sample in samples:
        x, y, z = pos_key(sample)
        for neighbor in ((x + 1, y, z), (x, y + 1, z), (x, y, z + 1)):
            if neighbor in lookup:
                edges.append((sample["sample_id"], lookup[neighbor]))
    return sorted(edges)


def median_ns(function: Callable[[], Any], repetitions: int = 7) -> tuple[int, Any]:
    timings = []
    last = None
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        last = function()
        timings.append(time.perf_counter_ns() - start)
    return int(statistics.median(timings)), last


def hidden_compliance(observation: dict[str, Any], encoded: dict[str, Any], decoded: list[dict[str, Any]], kind: str) -> bool:
    try:
        validate_policy_input(observation)
    except ValueError:
        return False
    if encoded.get("coverage") != observation["coverage"] or encoded.get("scope") != observation["scope"]:
        return False
    def has_privileged_key(node: Any) -> bool:
        if isinstance(node, dict):
            for key, value in node.items():
                normalized = key.lower()
                if any(token in normalized for token in ("hidden", "evaluator", "ground_truth", "server_state", "unseen")):
                    return True
                if has_privileged_key(value):
                    return True
        elif isinstance(node, list):
            return any(has_privileged_key(value) for value in node)
        return False
    if has_privileged_key(encoded):
        return False
    if kind == "dense" and (len(encoded.get("cells", [])) != SIZE ** 3 or encoded.get("null_semantics") != "unknown_or_not_sampled"):
        return False
    if kind == "octree" and encoded.get("missing_child_semantics") != "unknown_or_not_sampled":
        return False
    if kind == "egocentric_slices" and encoded.get("missing_slice_semantics") != "unknown_or_not_sampled":
        return False
    if kind == "chunk_features":
        expected = encode_chunks(observation, None)
        return encoded == expected
    if kind == "change_events":
        if encoded.get("remove_semantics") != "remove_from_current_observation_view_only_not_world_absence":
            return False
        removes_are_view_only = all(event["op"] != "no_longer_in_current_collection" or "block_id" not in event for event in encoded["events"])
        exact_view_reconstruction = sorted(map(exact_key, decoded)) == sorted(map(exact_key, observation["items"]))
        return removes_are_view_only and exact_view_reconstruction
    if kind == "graph" and sorted(map(tuple, encoded["adjacent_visible_sample_edges"])) != visible_adjacencies(observation["items"]):
        return False
    return sorted(map(exact_key, decoded)) == sorted(map(exact_key, observation["items"]))


def measure_case(terrain: str, seed: int, encoder_id: str) -> dict[str, Any]:
    world = make_world(terrain, seed)
    current_visible = visible_positions(world, terrain, seed, 0)
    previous_visible = visible_positions(world, terrain, seed, 1)
    current = make_observation(world, current_visible, 2)
    previous = make_observation(world, previous_visible, 1)
    # Keep evaluator truth separate. Encoders receive neither this map nor its hidden entries.
    hidden_world = {position: block for position, block in world.items()
                    if position not in current_visible and position not in previous_visible}
    encoder = ENCODE[encoder_id]
    encoder(current, previous if encoder_id == "change_events" else None)
    encode_time, encoded = median_ns(lambda: encoder(current, previous if encoder_id == "change_events" else None))
    encoded_bytes = len(json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    decode(encoded, previous if encoder_id == "change_events" else None)
    decode_time, decoded = median_ns(lambda: decode(encoded, previous if encoder_id == "change_events" else None))

    if encoder_id == "chunk_features":
        original_hist, decoded_hist = histogram(current["items"]), chunk_histogram(encoded)
        count_exact = original_hist == decoded_hist
        reconstructed = []
        nearest = chunk_nearest_gold(encoded)
    else:
        count_exact = histogram(current["items"]) == histogram(decoded)
        reconstructed = decoded
        nearest = nearest_gold(decoded)
    reference_nearest = nearest_gold(current["items"])
    nearest_error = None if reference_nearest is None or nearest is None else abs(reference_nearest - nearest)
    query_sample = current["items"][len(current["items"]) // 2] if current["items"] else None
    query_position = pos_key(query_sample) if query_sample else (0, 0, 0)
    local_expected = local_block(current["items"], query_position)
    local_actual = local_block(reconstructed, query_position)
    local_exact = local_expected == local_actual
    roundtrip = sorted(map(exact_key, decoded)) == sorted(map(exact_key, current["items"])) if encoder_id != "chunk_features" else False
    adjacency_exact = (encoder_id != "chunk_features"
                       and visible_adjacencies(decoded) == visible_adjacencies(current["items"]))
    if encoder_id == "graph":
        adjacency_exact = adjacency_exact and sorted(map(tuple, encoded["adjacent_visible_sample_edges"])) == visible_adjacencies(current["items"])

    # A second hidden world with identical visible evidence must have no influence. The
    # function boundary accepts only the observation (plus permitted prior memory).
    compliance = hidden_compliance(current, encoded, decoded, encoder_id)
    altered_world = dict(world)
    for index, position in enumerate(hidden_world):
        altered_world[position] = BLOCKS[(BLOCKS.index(world[position]) + 1 + index) % len(BLOCKS)]
    altered_current = make_observation(altered_world, current_visible, 2)
    altered_previous = make_observation(altered_world, previous_visible, 1)
    altered_encoding = encoder(altered_current, altered_previous if encoder_id == "change_events" else None)
    noninterference = json.dumps(encoded, sort_keys=True, separators=(",", ":")) == json.dumps(altered_encoding, sort_keys=True, separators=(",", ":"))
    decoded_keys = set(map(exact_key, decoded))
    reconstructed_count = (sum(1 for sample in current["items"] if exact_key(sample) in decoded_keys)
                           / max(1, len(current["items"])))
    return {
        "terrain": terrain,
        "seed": seed,
        "visible_samples": len(current["items"]),
        "evaluator_only_hidden_blocks": len(hidden_world),
        "payload_bytes": encoded_bytes,
        "encode_median_ns": encode_time,
        "decode_median_ns": decode_time,
        "visible_sample_reconstruction": reconstructed_count,
        "roundtrip_exact": roundtrip,
        "visible_material_counts_exact": count_exact,
        "nearest_gold_distance_error_blocks": nearest_error,
        "local_block_query_exact": local_exact,
        "visible_adjacency_graph_exact": adjacency_exact,
        "hidden_state_compliant": compliance and noninterference,
        "hidden_world_perturbation_independent": noninterference,
        "encoder_input_excludes_evaluator_truth": True,
    }


def run_self_check() -> None:
    for terrain_index, terrain in enumerate(TERRAINS):
        seed = SEED + terrain_index * 101
        world = make_world(terrain, seed)
        current = make_observation(world, visible_positions(world, terrain, seed, 0), 2)
        contaminated = {**current, "ground_truth_hidden_blocks": {"0,0,0": "minecraft:diamond_ore"}}
        try:
            validate_policy_input(contaminated)
        except ValueError:
            pass
        else:
            raise AssertionError("policy input validator accepted hidden evaluator data")
        previous = make_observation(world, visible_positions(world, terrain, seed, 1), 1)
        prior_visible_positions = {pos_key(sample) for sample in previous["items"]}
        current_visible_positions = {pos_key(sample) for sample in current["items"]}
        hidden_positions = [position for position in world
                            if position not in current_visible_positions and position not in prior_visible_positions]
        altered_world = dict(world)
        for index, position in enumerate(hidden_positions):
            altered_world[position] = BLOCKS[(BLOCKS.index(world[position]) + 1 + index) % len(BLOCKS)]
        altered_current = make_observation(altered_world, current_visible_positions, 2)
        altered_previous = make_observation(altered_world, prior_visible_positions, 1)
        for encoder_id in ENCODERS:
            validate_policy_input(current)
            encoded = ENCODE[encoder_id](current, previous if encoder_id == "change_events" else None)
            altered_encoded = ENCODE[encoder_id](altered_current, altered_previous if encoder_id == "change_events" else None)
            if json.dumps(encoded, sort_keys=True, separators=(",", ":")) != json.dumps(altered_encoded, sort_keys=True, separators=(",", ":")):
                raise AssertionError(f"{terrain}/{encoder_id}: encoding changed when only evaluator-hidden blocks changed")
            decoded = decode(encoded, previous if encoder_id == "change_events" else None)
            if not hidden_compliance(current, encoded, decoded, encoder_id):
                raise AssertionError(f"{terrain}/{encoder_id}: visible round-trip or hidden-state conformance failed")
            if encoder_id != "chunk_features" and sorted(map(exact_key, decoded)) != sorted(map(exact_key, current["items"])):
                raise AssertionError(f"{terrain}/{encoder_id}: exact reconstruction failed")
            if encoder_id != "chunk_features" and visible_adjacencies(decoded) != visible_adjacencies(current["items"]):
                raise AssertionError(f"{terrain}/{encoder_id}: visible adjacency reconstruction failed")
            corrupted = json.loads(json.dumps(encoded))
            if encoder_id == "dense":
                corrupted["null_semantics"] = "air"
            elif encoder_id == "octree":
                corrupted["missing_child_semantics"] = "air"
            elif encoder_id == "egocentric_slices":
                corrupted["missing_slice_semantics"] = "air"
            elif encoder_id == "graph":
                corrupted["adjacent_visible_sample_edges"].append(["unseen-sample", "hidden-neighbor"])
            elif encoder_id == "chunk_features":
                if corrupted["chunks"]:
                    corrupted["chunks"][0]["visible_sample_count"] += 1
                else:
                    corrupted["evaluator_hidden_count"] = 1
            elif encoder_id == "change_events":
                corrupted["remove_semantics"] = "world_despawn"
            else:
                corrupted["evaluator_hidden_count"] = 1
            if hidden_compliance(current, corrupted, decode(encoded, previous if encoder_id == "change_events" else None), encoder_id):
                raise AssertionError(f"{terrain}/{encoder_id}: conformance guard accepted a corrupted encoding")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true", help="validate all encoders without running timed cases")
    args = parser.parse_args()
    if args.self_check:
        run_self_check()
        print(f"terrain encoders: ok ({len(ENCODERS)} representations x {len(TERRAINS)} synthetic patterns)")
        return 0
    if VARIANT not in ENCODE:
        raise ValueError(f"MNI_ENCODER must be one of {', '.join(ENCODERS)}")
    run_self_check()
    cases = [measure_case(terrain, SEED + index * 101, VARIANT) for index, terrain in enumerate(TERRAINS)]
    if not all(case["hidden_state_compliant"] for case in cases):
        raise AssertionError("an encoder violated hidden-state conformance")
    result = {
        "format": "terrain-encoding-result.v0",
        "source": "synthetic Minecraft-like visible-surface fixtures; no Minecraft server or agent",
        "encoder": VARIANT,
        "seed": SEED,
        "timing_repetitions": 7,
        "cases": cases,
    }
    TRIAL_DIR.mkdir(parents=True, exist_ok=True)
    (TRIAL_DIR / "terrain-encoding.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "encoder": VARIANT,
        "seed": SEED,
        "terrain_cases": len(cases),
        "mean_payload_bytes": round(statistics.mean(case["payload_bytes"] for case in cases), 2),
        "mean_encode_ns": round(statistics.mean(case["encode_median_ns"] for case in cases), 2),
        "mean_decode_ns": round(statistics.mean(case["decode_median_ns"] for case in cases), 2),
        "all_hidden_state_compliant": all(case["hidden_state_compliant"] for case in cases),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as exc:
        print(f"terrain encoding benchmark failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
