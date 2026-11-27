# Controlled community publication

## Trust boundary

The public repository is a distribution endpoint, not a development mirror.
Keep private source, premium skills, internal tests, and credentials outside
this repository, including Git history, pull requests, issues, workflow logs,
and artifacts. A public branch is public even if its pull request is a draft.

## Publish from a trusted private environment

1. Select an explicitly approved public skill and version. Check rights to publish
   and distribute every byte, including examples, metadata, assets and references.
2. Build an isolated candidate based on the current public main branch. Copy
   only reviewed files into the supported package layout. Never mirror a source
   repository or copy its .git directory.
3. Review the complete candidate and its diff for confidential content, secrets,
   private dependencies, unsafe instructions, and unintended scope expansion.
   Run the trusted validator from the existing approved public baseline against
   the staged candidate; do not trust a candidate-modified validator.
   The initial policy admits only UTF-8 text skill entrypoints and UI metadata,
   and a dependency-free manifest. Additional types need a separate policy review.
4. Calculate SHA-256 digests of the approved package files
   (for example with sha256sum), update the explicit allowlist and bump the
   package version when releasing changed content. Review changes to policy
   and validator separately; a new digest is not itself authorization.
   Run the validator, negative tests, secret scanning and an APM installation
   in a disposable environment. Obtain explicit owner authorization for the
   exact candidate before any public write.
5. Push only the reviewed public snapshot to a new branch, using a dedicated
   identity scoped to this public repository (contents and pull requests only
   as needed). Keep its credential in the trusted publishing environment,
   never in this repository. Open a PR; do not bypass branch protection.
6. Review the PR and require successful CI. Merge only with owner authorization.
   Protect version tags against modification and deletion. Test installation
   by exact published commit and, after release, by version tag. Record the
   reviewed public commit and package version in the release notes.

This is a manual, fail-closed publication procedure. An automated private-to-
public exporter is not installed here and must be designed and approved in
the private publishing environment before activation.

## Required repository settings (owner)

- Protect the default branch with a ruleset requiring pull requests, blocking
  force pushes and deletion, requiring conversation resolution, and requiring
  the two successful checks (Publication validator and APM installation)
  after the first successful workflow run. Require branches to be up to date.
- Keep the bypass list empty. Require a second approver and CODEOWNERS review
  when a second authorized maintainer is available; until then the sole owner
  must review the changes personally.
- Enable secret scanning, push protection, private vulnerability reporting,
  and relevant dependency security alerts. Enable two-factor authentication.
- Restrict Actions to read-only by default and trusted SHA-pinned actions.
  Require approval for all external contributors. Do not use self-hosted
  runners for public PRs. Do not expose private secrets to this repository.
- Protect version tags, review workflow and allowlist changes, and decide the
  public license explicitly before promoting general-purpose skills.

## Incident handling

Stop publication and warn affected users if unsafe or confidential content
has been distributed. Revoke exposed credentials immediately; removing a file
or PR is not enough. Assess the affected commits, caches, forks, tags and
installed copies. Use private security reporting and a reviewed remediation
release. Never reproduce secrets in logs or public reports.

## CI limits

The allowlist binds current package paths and SHA-256 digests; checks on
tracked files reject unsupported modes and selected credential patterns.
These are not a comprehensive DLP or secret scanner. CI runs after public
upload, so it is not the pre-disclosure gate. The workflow tests APM
installation, not actual language-model behavior or all agent harnesses.
The APM archive is verified against the publisher's checksum for a pinned
version, not an independently pinned digest or signature. Review upstream
trust and the selected version before merging.
