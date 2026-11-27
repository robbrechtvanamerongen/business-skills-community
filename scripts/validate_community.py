"""Validate the staged public snapshot; never print matched content or secrets."""
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

POLICY = '.github/publication-allowlist.json'
INFRA = frozenset({
    'README.md', 'SECURITY.md', '.github/CODEOWNERS', POLICY,
    '.github/workflows/community-validation.yml',
    'docs/publication-process.md', 'scripts/validate_community.py',
    'tests/test_validate_community.py',
})
SKILL_PATH = re.compile(r'\.apm/skills/([a-z0-9]+(?:-[a-z0-9]+)*)/(SKILL\.md|agents/openai\.yaml)')
SECRET_PATTERNS = (
    re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----'),
    re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}'),
)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate allowlist key')
        result[key] = value
    return result


def validate(entries):
    """Entries map tracked paths to (Git mode, blob bytes). Return safe errors."""
    errors = []
    try:
        policy = json.loads(entries[POLICY][1], object_pairs_hook=unique_pairs)
        if set(policy) != {'schema', 'package_files'} or policy['schema'] != 1:
            raise ValueError('invalid policy schema')
        approved = policy['package_files']
        if not isinstance(approved, dict) or 'apm.yml' not in approved:
            raise ValueError('missing package manifest')
        if any((p != 'apm.yml' and not SKILL_PATH.fullmatch(p)) or
               not isinstance(d, str) or not re.fullmatch(r'[0-9a-f]{64}', d)
               for p, d in approved.items()):
            raise ValueError('invalid package allowlist')
        skills = {SKILL_PATH.fullmatch(p).group(1) for p in approved if p != 'apm.yml'}
        if not skills or any(f'.apm/skills/{s}/SKILL.md' not in approved for s in skills):
            raise ValueError('missing skill entrypoint')
    except (KeyError, ValueError, TypeError, UnicodeError):
        return ['Invalid or missing publication allowlist.']

    if set(entries) != INFRA | set(approved):
        errors.append('Tracked file inventory differs from the explicit allowlist.')
    texts = {}
    for path, (mode, data) in entries.items():
        if mode != '100644' or len(data) > 256 * 1024:
            errors.append('Unsupported file mode or size.')
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeError:
            errors.append('Non-UTF-8 content is forbidden.')
            continue
        if any(unicodedata.category(c) in {'Cc', 'Cf'} and c not in '\n\r\t' for c in text):
            errors.append('Hidden/control characters are forbidden.')
        if any(p.search(text) for p in SECRET_PATTERNS):
            errors.append('Possible credential detected; investigate privately.')
        if path in approved and hashlib.sha256(data).hexdigest() != approved[path]:
            errors.append('Package content does not match the approved SHA-256 digest.')
        texts[path] = text

    # Deliberately support only a small, dependency-free manifest schema.
    manifest = texts.get('apm.yml', '').splitlines()
    fields = {}
    for line in manifest:
        match = re.fullmatch(r'(name|version|description|author): ([A-Za-z0-9][A-Za-z0-9 .,_-]*)', line)
        if not match or match[1] in fields:
            errors.append('Unsupported or duplicate manifest field; dependencies are forbidden.')
            continue
        fields[match[1]] = match[2]
    if (set(fields) != {'name', 'version', 'description', 'author'} or
            fields.get('name') != 'business-skills-community' or
            not re.fullmatch(r'\d+\.\d+\.\d+', fields.get('version', ''))):
        errors.append('Manifest identity or version is invalid.')
    for skill in sorted(skills):
        text = texts.get(f'.apm/skills/{skill}/SKILL.md', '')
        if not re.match(r'\A---\nname: ' + re.escape(skill) + r'\ndescription: [^\n]+\n---\n\s*\S', text):
            errors.append('Skill frontmatter or entrypoint body is invalid.')
    return errors


def staged_entries(root):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root)
    entries = {}
    for row in git('ls-files', '--stage', '-z').split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, digest, stage = meta.decode('ascii').split()
        path = name.decode('utf-8')
        if stage != '0' or path in entries:
            raise ValueError('unmerged index')
        if mode != '100644' or int(git('cat-file', '-s', digest)) > 256 * 1024:
            entries[path] = (mode, b'\0' * (256 * 1024 + 1))
        else:
            entries[path] = (mode, git('cat-file', 'blob', digest))
    return entries


def main():
    try:
        errors = validate(staged_entries(Path(__file__).resolve().parents[1]))
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        errors = ['Unable to inspect the Git index safely.']
    for error in sorted(set(errors)):
        print(error, file=sys.stderr)
    if errors:
        return 1
    print('Community publication validation passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
