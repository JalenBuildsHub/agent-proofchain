# Contributing

Agent ProofChain is an alpha security boundary. Contributions are welcome through review, but a
source checkout or draft pull request is not a public-release or production-readiness claim.

1. Open an issue describing the behavior, threat, or evaluation gap.
2. Use synthetic identities, repositories, prompts, and credentials.
3. Add or update focused tests.
4. Use Python 3.11 through 3.14 and install the exact reviewed tools with
   `python -m pip install -e ".[dev]"`.
5. Run:

   ```bash
   python -m ruff format --check .
   python -m ruff check .
   python -m mypy
   python -m coverage run -m pytest
   python -m coverage report
   bandit -q -r src -ll -ii
   pip-audit --strict --skip-editable
   python -m build
   python -m twine check dist/*
   python scripts/verify-release.py dist
   ```

6. Exercise the built wheel in a clean environment rather than relying only on an editable
   source install.
7. Document limitations and false-positive risk for new detection rules.

Never submit private prompts, secrets, customer data, internal paths, or production incident logs.
Never weaken source attribution, adapter task-intent validation, read-only ledger verification,
release ancestry, artifact provenance, or least-privilege workflow permissions to make a test pass.
