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
        self.assertEqual(len(items), 330)
        self.assertEqual(len(BASE['domains']), 15)
        self.assertEqual(len(milestones), 12)
        self.assertEqual(progress.metrics(BASE)['researchCoverage'], 1.0)

    def test_gameplay_competencies_have_independent_in_game_gates(self):
        self.validate()
        competencies = progress.gameplay_competencies(BASE)
        self.assertEqual(len(competencies), 62)
        self.assertEqual({row['competency']['group'] for _, row in competencies}, progress.COMPETENCY_GROUPS)
        for _, row in competencies:
            self.assertTrue(row['dependencies'])
            self.assertTrue(row['competency']['scenario'])
            self.assertTrue(row['competency']['failureBoundary'])
            self.assertEqual(row['status']['validation'], 'untested')

    def test_missing_or_invalid_gameplay_gate_is_rejected(self):
        data = copy.deepcopy(BASE)
        item(data, 'GP-001').pop('competency')
        with self.assertRaisesRegex(progress.InvalidProgress, 'lacks independently testable competency'):
            self.validate(data)
        data = copy.deepcopy(BASE)
        item(data, 'GP-001')['competency']['scenario'] = 'brief'
        with self.assertRaisesRegex(progress.InvalidProgress, 'string shorter than minLength'):
            self.validate(data)

    def test_duplicate_model_candidate_name_is_rejected(self):
        data = copy.deepcopy(BASE)
        data['modelCandidates'][-1]['name'] = data['modelCandidates'][0]['name']
        with self.assertRaisesRegex(progress.InvalidProgress, 'duplicated model architecture'):
            self.validate(data)

    def test_new_scope_maps_into_existing_milestones_without_credit(self):
        self.validate()
        mapped = {ident for m in BASE['milestones'] for ident in m['items']}
        for ident in ['GP-001','GP-027','GP-037','GP-060','GP-061','GP-062','DP-001','DP-012','TM-20','TM-21','TM-22','TM-23']:
            self.assertIn(ident, mapped)
            self.assertEqual(item(BASE, ident)['status']['implementation'], 'not_implemented')
        self.assertEqual(progress.metrics(BASE)['demonstratedCapabilities'], 0.0)

    def test_new_scope_has_negative_boundaries_and_no_status_promotion(self):
        added_ids = ['PE-014','MO-018','MO-019','MO-020','MO-021','LR-023','LR-024',
                     'CO-016','BU-016','BU-017','BU-018','ME-017','IN-016',
                     'EV-018','EV-019','MA-015','GP-061','GP-062','TM-22','TM-23']
        self.validate()
        for ident in added_ids:
            row = item(BASE, ident)
            self.assertTrue(row['dependencies'], ident)
            self.assertGreaterEqual(len(row['acceptanceCriteria']), 3, ident)
            self.assertEqual(row['status']['research'], 'not_investigated', ident)
            self.assertEqual(row['status']['experimentalOutcome'], 'not_assessed', ident)
            self.assertEqual(row['status']['implementation'], 'not_implemented', ident)
            self.assertEqual(row['status']['validation'], 'untested', ident)
        for ident in ('GP-061','GP-062'):
            self.assertIn('Survival', item(BASE, ident)['competency']['evidenceRequired'])

    def test_unexplored_catalogue_is_not_research_completion(self):
        self.assertEqual(item(BASE, 'MI-01')['status']['research'], 'not_investigated')
        self.assertEqual(progress.metrics(BASE)['researchCompletion'], 0.0)

    def test_legacy_research_protocols_have_distinct_falsifiable_trials(self):
        self.validate()
        avenues = [row for domain in BASE['domains'] for row in domain['avenues']]
        protocols = [row for row in avenues if 'Reproduce: ' in row['methodology']]
        self.assertEqual(len(protocols), 150)
        self.assertEqual(len({row['methodology'] for row in protocols}), 150)
        for row in protocols:
            self.assertIn('Compare: ', row['methodology'])
            self.assertIn('Record: ', row['methodology'])
            self.assertIn('Inject boundary: ', row['methodology'])
            self.assertGreaterEqual(len(row['acceptanceCriteria']), 4)
            self.assertTrue(any('boundary trials' in task for task in row['remainingWork']))
            self.assertEqual(row['status']['research'], 'not_investigated')
            self.assertEqual(row['status']['validation'], 'untested')

    def test_reintroduced_generic_avenue_template_is_rejected(self):
        data = copy.deepcopy(BASE)
        item(data, 'MI-004')['methodology'] = 'Define a falsifiable protocol for a generic project.'
        with self.assertRaisesRegex(progress.InvalidProgress, 'generic research boilerplate'):
            self.validate(data)

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

    def test_unmerged_closed_pr_cannot_receive_integrated_credit(self):
        data = copy.deepcopy(BASE)
        data['unmergedWork'][0]['integrated'] = True
        with self.assertRaisesRegex(progress.InvalidProgress, 'unmerged work cannot receive integrated/shipped credit'):
            self.validate(data)

    def test_live_pr_number_and_count_snapshots_must_match(self):
        data = copy.deepcopy(BASE)
        data['githubState']['openPullRequestNumbers'] = [122]
        with self.assertRaisesRegex(progress.InvalidProgress, 'GitHub openPullRequestNumbers snapshot'):
            self.validate(data)
        data = copy.deepcopy(BASE)
        data['unmergedWork'][0]['state'] = 'open'
        with self.assertRaisesRegex(progress.InvalidProgress, 'GitHub PR count disagrees'):
            self.validate(data)

    def test_historical_pr_is_reported_as_closed_without_main_credit(self):
        result = progress.render(BASE)
        dashboard = result[ROOT / 'docs/PROGRESS.md']
        self.assertIn('open PRs: **0**', dashboard)
        self.assertIn('## Unmerged PR history', dashboard)
        self.assertIn('](https://github.com/xdCloudy/minecraft-native-intelligence/pull/122) closed', dashboard)
        self.assertNotIn('## Open PR snapshot', dashboard)

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
        self.assertIn(ROOT / 'docs/MINECRAFT_COMPETENCY_MATRIX.md', first)
        self.assertEqual(progress.apply_outputs(first, check=True), [])


if __name__ == '__main__':
    unittest.main()
