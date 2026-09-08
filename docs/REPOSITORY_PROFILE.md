# Repository profile checklist

These settings are applied through GitHub repository administration rather than source control. Review them after the stacked pull requests are merged.

## Description

Recommended repository description:

> Provider-neutral admission decisions and tamper-evident action receipts for AI agents.

Keep the description narrower than the aspirational protocol vision.

## Website

Leave the website field empty until there is a maintained documentation or product URL. Do not point the repository at a generic studio homepage unless that page contains current project documentation.

## Topics

Recommended topics:

```text
ai-agents
agent-security
authorization
audit-logs
audit-trail
provenance
prompt-injection
security
receipts
python
open-source
ai-safety
```

GitHub limits repository topics; choose the most accurate terms rather than every adjacent trend.

## Social preview

Source artwork:

```text
docs/assets/agent-proofchain-social-preview.svg
```

Export it to a 1280 × 640 PNG and upload it through the repository's social-preview settings. Verify text legibility at small card sizes before approval.

The preview deliberately communicates:

```text
Authenticate → Decide → Verify
```

It does not claim certification, complete prompt-injection protection, or production adoption.

## Features

Recommended after maintainer approval:

- Issues: enabled;
- Discussions: enabled when someone can respond consistently;
- Projects: optional;
- Wiki: disabled unless maintained;
- Sponsorships: unset until a real funding destination exists.

## Security settings

Enable where available:

- private vulnerability reporting;
- dependency graph;
- Dependabot alerts;
- Dependabot security updates;
- secret scanning;
- push protection;
- code scanning after the Scorecard workflow lands on the default branch.

## Branch protection

Protect `main` after the stacked pull requests are merged and CI workflow names stabilize.

Recommended baseline:

- pull requests required;
- at least one approving review when another qualified reviewer is available;
- conversation resolution required;
- required CI, action-smoke, and clean-install checks;
- branch must be current before merge;
- force pushes and deletion disabled;
- administrators follow the same policy unless an emergency procedure is documented.

## Release profile

Do not publish to PyPI or GitHub Marketplace merely because the repository page looks complete. Follow `docs/RELEASE_CHECKLIST.md`, use an immutable reviewed commit, and verify the package and action from a clean environment first.
