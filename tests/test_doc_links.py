"""Regression tests for repository-local documentation link validation."""
import tempfile
import unittest
from pathlib import Path

from tools.check_doc_links import anchors, check, visible_lines


class DocumentationLinkTests(unittest.TestCase):
    def test_code_fences_and_duplicate_heading_anchors(self):
        source = '# A title\n## Repeat\n## Repeat\n<a id="custom-id"></a>\n```md\n[bogus](missing.md)\n```\n'
        self.assertEqual(anchors(source), {'a-title', 'repeat', 'repeat-1', 'custom-id'})
        self.assertFalse(any('bogus' in line for line in visible_lines(source)))

    def test_relative_paths_and_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'docs').mkdir()
            (root / 'docs/target.md').write_text('# Present\n', encoding='utf-8')
            (root / 'README.md').write_text(
                '[okay](docs/target.md#present) [bad](docs/target.md#absent) '
                '[missing](docs/nope.md) [remote](https://example.com/foo)\n',
                encoding='utf-8',
            )
            issues = check(root)
            self.assertEqual(len(issues), 2)
            self.assertTrue(any('missing anchor' in issue for issue in issues))
            self.assertTrue(any('missing path' in issue for issue in issues))


if __name__ == '__main__':
    unittest.main()
