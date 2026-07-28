# Release checklist

This checklist separates code completion from a public release. Feature pull requests must not silently publish packages, tags, marketplace listings, or security claims.

## 1. Scope and evidence

- [ ] Release scope is documented in `CHANGELOG.md`.
- [ ] Public claims match demonstrated behavior.
- [ ] Threat model and limitations reflect the release.
- [ ] Receipt, vector, CLI, and adapter compatibility changes are identified.
- [ ] Synthetic fixtures contain no secrets, customer data, private prompts, or internal paths.
- [ ] Independent fixture or methodology review is linked when claimed.

## 2. Validation

- [ ] Ruff passes.
- [ ] Full pytest suite passes.
- [ ] Wheel and source distribution build successfully.
- [ ] `proofchain demo` passes from a clean installation.
- [ ] Python conformance verifier accepts the published vector.
- [ ] JavaScript verifier returns the same final chain hash.
- [ ] Admission evaluation reports zero unexplained fixture mismatches.
- [ ] Tamper evaluation reports all expected outcomes and the final-truncation limitation.
- [ ] Ubuntu and Windows CI evidence artifacts are retained for review.
- [ ] Reusable GitHub Action smoke tests pass on Ubuntu and Windows.

## 3. Security and supply chain

- [ ] Dependencies and GitHub Actions are reviewed and pinned appropriately.
- [ ] OpenSSF Scorecard results are reviewed after the workflow runs on the default branch.
- [ ] Repository secret scanning and dependency alerts are enabled where available.
- [ ] No generated credentials, databases, or evidence containing private data are committed.
- [ ] Package contents are inspected before publication.
- [ ] Release credentials use trusted publishing or another short-lived mechanism; no long-lived token is committed.
- [ ] Security contact and private-reporting path are working.

## 4. Community and documentation

- [ ] README quick start works in a clean environment.
- [ ] Installation, action, protocol, architecture, contributing, support, and conduct links resolve.
- [ ] Issue and pull-request templates are visible on the default branch.
- [ ] Repository description, topics, and social preview are approved.
- [ ] A maintainer is assigned to triage new issues and security reports.
- [ ] Good-first-issue candidates are real, bounded, and supported.

## 5. Publication decision

- [ ] Version number is approved.
- [ ] Release commit is reviewed and immutable.
- [ ] Tag is signed or otherwise attributable under the studio policy.
- [ ] GitHub release notes are approved.
- [ ] PyPI publication is separately authorized.
- [ ] GitHub Marketplace publication is separately authorized.
- [ ] No external announcement is made before install and artifact links are verified.

## 6. Post-release verification

- [ ] Install the published package into a new environment.
- [ ] Run `proofchain demo`.
- [ ] Run the published conformance vector.
- [ ] Verify repository and package version metadata.
- [ ] Verify release artifacts and checksums.
- [ ] Open a clean-install receipt or issue from an account outside the maintainer environment when available.
- [ ] Record defects and rollback or yank criteria.

## Stop conditions

Do not publish when:

- CI is not green;
- release contents differ from the reviewed commit;
- a security or privacy concern is unresolved;
- the version or compatibility story is ambiguous;
- documentation claims external review, adoption, or certification that has not occurred;
- publication credentials or rollback authority are unclear.
