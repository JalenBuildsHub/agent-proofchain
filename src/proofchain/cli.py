"""Command-line interface for portable admission decisions and ledger verification."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .admission import AdmissionRequest, evaluate
from .evals import load_fixtures, render_evaluation_markdown, run_evaluation
from .ledger import ReceiptLedger
from .policy import AdmissionPolicy
from .tamper import render_tamper_markdown, run_tamper_evaluation, write_report


def _write_text(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofchain")
    parser.add_argument("--version", action="version", version=f"proofchain {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("--policy", required=True)
    evaluate_parser.add_argument("--request", required=True)
    evaluate_parser.add_argument("--ledger", required=True)

    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--ledger", required=True)

    eval_parser = sub.add_parser("eval")
    eval_parser.add_argument("--policy", required=True)
    eval_parser.add_argument("--fixtures", required=True)
    eval_parser.add_argument("--output")
    eval_parser.add_argument("--markdown-output")

    tamper_parser = sub.add_parser("tamper-eval")
    tamper_parser.add_argument("--output")
    tamper_parser.add_argument("--markdown-output")
    return parser


def _execute(args: argparse.Namespace) -> int:
    if args.command == "verify":
        ledger = ReceiptLedger(args.ledger)
        result = ledger.verify()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1

    if args.command == "eval":
        policy = AdmissionPolicy.from_json(args.policy)
        result = run_evaluation(policy, load_fixtures(args.fixtures))
        rendered = json.dumps(result, indent=2, sort_keys=True)
        if args.output:
            _write_text(args.output, rendered + "\n")
        if args.markdown_output:
            _write_text(args.markdown_output, render_evaluation_markdown(result))
        print(rendered)
        return 0 if result["correct"] == result["total"] else 1

    if args.command == "tamper-eval":
        result = run_tamper_evaluation()
        if args.output:
            write_report(args.output, result)
        if args.markdown_output:
            _write_text(args.markdown_output, render_tamper_markdown(result))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["all_expected_outcomes_matched"] else 1

    policy = AdmissionPolicy.from_json(args.policy)
    request = AdmissionRequest.from_dict(json.loads(Path(args.request).read_text(encoding="utf-8")))
    decision = evaluate(request, policy)
    ledger = ReceiptLedger(args.ledger)
    receipt = ledger.append(decision)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if decision.allowed else 2


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _execute(args)
    except (json.JSONDecodeError, OSError, sqlite3.Error, TypeError, ValueError):
        print(
            "proofchain: invalid input or unreadable ledger; no action was admitted",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
