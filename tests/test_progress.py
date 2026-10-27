"""Integrity tests for the canonical Minecraft Native Intelligence progress system."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('progress', ROOT / 'tools/progress.py')
assert spec and spec.loader
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)
BASE = json.loads((ROOT / 'docs/progress/progress.json').read_text(encoding='utf-8'))
SCHEMA = json.loads((ROOT / 'docs/progress/progress.schema.json').read_text(encoding='utf-8'))


def item(data, ident):
    return next(row for _, row, _ in progress.all_items(data) if row['id'] == ident)


class ProgressTests(unittest.TestCase):
    def validate(self, data=None):
        return progress.validate(copy.deepcopy(data if data is not None else BASE), SCHEMA)

    def test_canonical_inventory_is_exhaustive_and_scored(self):
        items, _, milestones = self.validate()
        self.assertEqual(len(items), 236)
        self.assertEqual(len(BASE['domains']), 13)
        self.assertEqual(len(milestones), 12)
        self.assertEqual(progress.metrics(BASE)['researchCoverage'], 1.0)

    def test_unexplored_catalogue_is_not_research_completion(self):
        self.assertEqual(item(BASE, 'MI-01')['status']['research'], 'not_investigated')
        self.assertEqual(progress.metrics(BASE)['researchCompletion'], 0.0)

    def test_each_status_dimension_is_scored_independently(self):
        data = copy.deepcopy(BASE)
        row = item(data, 'MI-01')
        row['status']['research'] = 'research_concluded'
        row['status']['experimentalOutcome'] = 'negative'
        row['status']['implementation'] = 'not_implemented'
        before = progress.metrics(BASE)
        after = progress.metrics(data)
        self.assertGreater(after['researchCompletion'], before['researchCompletion'])
        self.assertEqual(after['implementationMaturity'], before['implementationMaturity'])
        self.assertEqual(after['demonstratedCapabilities'], 0.0)

    def test_unknown_evidence_is_rejected(self):
        data = copy.deepcopy(BASE)
        item(data, 'MI-01')['evidence'].append('missing-source')
        with self.assertRaisesRegex(progress.InvalidProgress, 'unknown evidence'):
            self.validate(data)

    def test_unrecognized_main_revision_is_rejected(self):
        data = copy.deepcopy(BASE)
        item(data, 'MI-01')['lastVerifiedRevision'] = '0' * 40
        with self.assertRaisesRegex(progress.InvalidProgress, 'untracked assessed revision'):
            self.validate(data)

    def test_missing_dependency_and_dependency_cycle_are_rejected(self):
        data = copy.deepcopy(BASE)
        item(data, 'MI-01')['dependencies'] = ['NO-999']
        with self.assertRaisesRegex(progress.InvalidProgress, 'missing dependency'):
            self.validate(data)
        data = copy.deepcopy(BASE)
        item(data, 'MI-01')['dependencies'] = ['MI-02']
        item(data, 'MI-02')['dependencies'] = ['MI-01']
        with self.assertRaisesRegex(progress.InvalidProgress, 'dependency cycle'):
            self.validate(data)

    def test_orphaned_evidence_is_rejected(self):
        data = copy.deepcopy(BASE)
        data['evidence'].append({'id': 'orphan', 'title': 'Unused', 'kind': 'paper', 'url': 'https://example.org'})
        with self.assertRaisesRegex(progress.InvalidProgress, 'orphan evidence'):
            self.validate(data)

    def test_status_vocabulary_is_schema_enforced(self):
        data = copy.deepcopy(BASE)
        item(data, 'MI-01')['status']['validation'] = 'shipped'
        with self.assertRaisesRegex(progress.InvalidProgress, 'outside enum'):
            self.validate(data)

    def test_open_pr_cannot_receive_integrated_credit(self):
        data = copy.deepcopy(BASE)
        data['unmergedWork'][0]['integrated'] = True
        with self.assertRaisesRegex(progress.InvalidProgress, 'open work cannot receive integrated/shipped credit'):
            self.validate(data)

    def test_branch_experiment_has_provenance_without_main_capability_credit(self):
        record = BASE['experimentRecords'][0]
        self.assertEqual(record['outcome'], 'inconclusive')
        self.assertEqual(record['trackedItemId'], 'PE-04')
        self.assertNotEqual(record['revision'], BASE['assessment']['defaultBranchRevision'])
        self.assertEqual(item(BASE, 'PE-04')['lastVerifiedRevision'], BASE['assessment']['defaultBranchRevision'])
        self.assertEqual(item(BASE, 'PE-04')['status']['implementation'], 'not_implemented')

    def test_scoped_milestones_map_all_item_kinds(self):
        item_ids = {row['id'] for _, row, _ in progress.all_items(BASE)}
        for milestone in BASE['milestones']:
            self.assertTrue(set(milestone['items']) <= item_ids)
        self.assertTrue(any(any(value.startswith('MC-') for value in m['items']) for m in BASE['milestones']))
        self.assertTrue(any(any(value.startswith('TM-') for value in m['items']) for m in BASE['milestones']))

    def test_scoring_rules_are_bounded_and_objective_weighted(self):
        self.assertAlmostEqual(sum(BASE['scoring']['overallScopedProgress'].values()), 1.0)
        self.assertGreater(BASE['scoring']['overallScopedProgress']['demonstratedCapability'], 0.5)
        for scores in BASE['scoring'].values():
            if isinstance(scores, dict):
                for value in scores.values():
                    if isinstance(value, (int, float)):
                        self.assertGreaterEqual(value, 0)
                        self.assertLessEqual(value, 1)

    def test_generator_check_does_not_modify_stale_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'generated.md'
            path.write_text('stale', encoding='utf-8')
            self.assertEqual(progress.apply_outputs({path: 'fresh'}, check=True), [path])
            self.assertEqual(path.read_text(encoding='utf-8'), 'stale')

    def test_generated_output_is_deterministic_and_current(self):
        first = progress.final_outputs(BASE, progress.render(BASE))
        second = progress.final_outputs(BASE, progress.render(BASE))
        self.assertEqual(first, second)
        self.assertEqual(progress.apply_outputs(first, check=True), [])


if __name__ == '__main__':
    unittest.main()
