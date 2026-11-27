import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_community import INFRA, POLICY, validate

SKILL = '.apm/skills/hello-world/SKILL.md'


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.entries = {path: ('100644', b'public') for path in INFRA}
        self.entries.update({
            'apm.yml': ('100644', b'name: business-skills-community\nversion: 0.1.0\ndescription: Public skills\nauthor: owner\n'),
            SKILL: ('100644', b'---\nname: hello-world\ndescription: Public test\n---\nHello\n'),
        })
        self.approve()

    def approve(self):
        files = {path: hashlib.sha256(self.entries[path][1]).hexdigest()
                 for path in ('apm.yml', SKILL)}
        self.entries[POLICY] = ('100644', json.dumps({'schema': 1, 'package_files': files}).encode())

    def test_valid(self):
        self.assertEqual(validate(self.entries), [])

    def test_unexpected_file(self):
        self.entries['private.md'] = ('100644', b'dummy')
        self.assertTrue(validate(self.entries))

    def test_missing_file(self):
        del self.entries[SKILL]
        self.assertTrue(validate(self.entries))

    def test_changed_skill(self):
        self.entries[SKILL] = ('100644', self.entries[SKILL][1] + b'new text')
        self.assertTrue(validate(self.entries))

    def test_dependency_even_if_approved(self):
        self.entries['apm.yml'] = ('100644', self.entries['apm.yml'][1] + b'dependencies: []\n')
        self.approve()
        self.assertTrue(validate(self.entries))

    def test_invalid_frontmatter_even_if_approved(self):
        self.entries[SKILL] = ('100644', b'not a skill')
        self.approve()
        self.assertTrue(validate(self.entries))

    def test_symlink(self):
        self.entries['README.md'] = ('120000', b'elsewhere')
        self.assertTrue(validate(self.entries))

    def test_fake_token_without_echo(self):
        token = b'gh' + b'p_' + b'A' * 36
        self.entries['README.md'] = ('100644', token)
        errors = validate(self.entries)
        self.assertIn('Possible credential detected; investigate privately.', errors)
        self.assertNotIn(token.decode(), str(errors))

    def test_hidden_character(self):
        self.entries['README.md'] = ('100644', 'public\u200b'.encode())
        self.assertTrue(validate(self.entries))

    def test_missing_allowlist(self):
        del self.entries[POLICY]
        self.assertTrue(validate(self.entries))


if __name__ == '__main__':
    unittest.main()
