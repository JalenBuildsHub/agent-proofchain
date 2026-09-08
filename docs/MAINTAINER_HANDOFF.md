# Maintainer handoff

This repository currently has four stacked draft pull requests. They were intentionally kept unmerged and unreleased so the maintainer can review each trust boundary separately.

## Review and merge order

### 1. PR #1 — v0.2 evaluation and evidence foundation

Review:

- admission metrics and reason-code contracts;
- 40-case synthetic corpus;
- runtime adapter trust boundary;
- tamper scenarios and final-truncation limitation;
- Windows SQLite portability fix.

Suggested merge method: squash into `main` after approval.

### 2. PR #2 — demo and open-source adoption foundation

After PR #1 merges:

1. retarget PR #2 to `main`;
2. confirm the resulting diff contains only PR #2's adoption and community work;
3. rerun CI;
4. squash after approval.

Review:

- network-free demo and privacy output;
- architecture and vision language;
- package metadata;
- contribution and reporting files;
- issue and pull-request templates;
- Scorecard workflow pins.

### 3. PR #3 — portable protocol and conformance

After PR #2 merges:

1. retarget PR #3 to `main`;
2. rerun CI;
3. verify Python and JavaScript produce the published chain head;
4. squash after protocol review.

Review:

- canonical JSON contract;
- receipt-v2 field and privacy rules;
- JSON Schemas;
- conformance vector;
- negative tests;
- limits around numeric and Unicode edge cases.

### 4. PR #4 — reusable action and launch readiness

After PR #3 merges:

1. retarget PR #4 to `main`;
2. rerun all three workflows;
3. verify action-smoke and clean-install artifacts;
4. review launch and release documents;
5. squash after approval.

Review:

- composite-action inputs and output path;
- action dependency pins;
- custom fixture privacy implications;
- clean-wheel installation;
- repository profile and social-preview source;
- external review intake;
- release and launch stop conditions.

## Why squash merges are recommended

The connector created focused commits per file and correction, which is useful during construction but too granular for long-term history. Squashing each reviewed PR preserves the four architectural stages without carrying dozens of implementation commits into `main`.

## Post-merge repository work

Source-controlled work cannot configure every GitHub setting. After all four PRs land:

- apply the description and topics in `docs/REPOSITORY_PROFILE.md`;
- export and upload the social preview;
- enable private vulnerability reporting and supported security features;
- stabilize required check names and protect `main`;
- enable Discussions only when maintainer response capacity exists;
- verify all documentation links from the default branch;
- run OpenSSF Scorecard from `main` and review the result;
- create real, bounded good-first issues after confirming labels and templates.

## Separate authorization gates

The following remain intentionally unperformed and need separate owner approval:

- marking the drafts ready for review;
- merging any pull request;
- creating a GitHub release;
- publishing to PyPI;
- publishing the action to GitHub Marketplace;
- announcing the project externally;
- contacting reviewers or communities;
- representing the project as externally validated, adopted, viral, or certified.

## Evidence before release

At minimum, follow `docs/RELEASE_CHECKLIST.md` and verify:

- all stacked PRs are represented correctly on `main`;
- clean-wheel installs pass outside an editable repository;
- Python and JavaScript conformance outputs agree;
- the one-command demo works from the release artifact;
- vulnerability reporting is staffed;
- public claims remain narrower than demonstrated evidence.
