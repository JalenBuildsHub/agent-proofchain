# Evidence-led launch plan

This plan prepares Agent ProofChain for discovery without promising virality or manufacturing adoption signals. No launch step should run before the stacked pull requests are reviewed, merged in order, and released under the release checklist.

## Positioning

Primary statement:

> Provider-neutral admission decisions and tamper-evident action receipts for AI agents.

Supporting statement:

> Authenticate the runtime in your host, evaluate its capability request under an explicit policy, and retain a privacy-safe receipt another implementation can verify.

Avoid positioning the project as:

- a complete AI security platform;
- guaranteed prompt-injection protection;
- agent authentication by itself;
- a sandbox or credential manager;
- a compliance certification;
- proof that an allowed action executed successfully.

## Launch assets

Required before announcement:

- green CI and action-smoke workflows;
- reviewed README and architecture diagram;
- sub-minute demo;
- reproducible evaluation artifacts;
- draft protocol and conformance vector;
- Python and JavaScript verification evidence;
- clear threat model and limitations;
- installation and GitHub Action guide;
- contribution, support, conduct, security, and citation files;
- reviewed repository description, topics, and social preview;
- immutable release or reviewed commit people can pin.

## Initial audiences

The best-fit early users are:

- engineers building tool-using AI agents;
- maintainers of agent frameworks and MCP servers;
- teams coordinating local and cloud coding agents;
- security engineers evaluating agent authorization boundaries;
- researchers creating agent-security benchmarks;
- open-source maintainers experimenting with verifiable automation.

## Launch sequence

### Phase 1 — quiet validation

1. Merge stacked pull requests in order after review.
2. Run clean installs on Ubuntu, Windows, and one non-maintainer environment.
3. Ask two or three technically qualified reviewers to challenge the protocol and fixtures.
4. Fix unclear documentation and false-confidence risks.
5. Publish one immutable alpha release only after explicit authorization.

### Phase 2 — technical release

Prepare one canonical release explanation containing:

- the concrete problem;
- the architecture diagram;
- the one-command demo;
- the receipt and chain contract;
- benchmark results and limitations;
- a copy-paste GitHub Action example;
- three bounded contribution opportunities.

Prefer a technical walkthrough over promotional copy.

### Phase 3 — community distribution

Potential channels, subject to owner approval and each community's rules:

- GitHub release and repository social preview;
- relevant agent-framework discussion forums;
- security and developer communities;
- an engineering article on Nymrel or JalenBuilds;
- a short demo video showing allow, deny, verify, and tamper results;
- direct requests for fixture review from maintainers with relevant expertise;
- open-source program applications after external evidence exists.

Do not mass-post identical messages or imply endorsement by model providers.

### Phase 4 — contributor conversion

New visitors should immediately see:

1. a runnable demo;
2. the problem and non-goals;
3. the current evidence;
4. one beginner contribution;
5. one deep protocol contribution;
6. how to report a vulnerability privately.

Maintain response quality. A burst of attention without issue triage damages the project.

## Candidate contribution campaigns

### Independent fixture pack

Invite contributors to add synthetic cases that expose false allows, false denies, or ambiguous reason-code contracts.

Success evidence:

- independently authored cases;
- reviewer rationale;
- benchmark version bump;
- public before/after metrics.

### Cross-language verifier

Invite implementations in Go, Rust, or TypeScript using the published vector.

Success evidence:

- exact expected chain head;
- negative mutation tests;
- documented canonicalization limitations;
- no dependency on the Python runtime.

### Runtime adapter examples

Invite small host-authenticated examples for major providers and local runtimes.

Success evidence:

- explicit transport-authentication boundary;
- payload identity cannot override host context;
- synthetic tests only;
- no provider compatibility or endorsement claim.

## Metrics that matter

Track:

- successful clean installs;
- external fixture authors;
- independent reviewers;
- repeat contributors;
- compatible verifier implementations;
- repositories pinning the action or package;
- issue-response time;
- false-allow and false-deny discoveries;
- security reports handled responsibly;
- releases with reproducible evidence.

Stars, forks, and traffic are useful discovery indicators but not proof of trust or adoption.

## Launch stop conditions

Pause launch when:

- public install instructions fail;
- CI or action smoke tests are not green;
- the release differs from reviewed code;
- vulnerability reporting is not staffed;
- benchmark claims exceed the evidence;
- a protocol review identifies unresolved canonicalization or privacy defects;
- there is no maintainer capacity to respond to contributors.
