"""Command-line interface for portable admission decisions and ledger verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .admission import AdmissionRequest, evaluate
from .evals import load_fixtures, run_evaluation
from .ledger import ReceiptLedger
from .policy import AdmissionPolicy


def main() -> int:
    parser = argparse.ArgumentParser(prog="proofchain")
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
    args = parser.parse_args()

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
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0 if result["false_allows"] == 0 and result["false_denies"] == 0 else 1

    policy = AdmissionPolicy.from_json(args.policy)
    request = AdmissionRequest.from_dict(json.loads(Path(args.request).read_text(encoding="utf-8")))
    decision = evaluate(request, policy)
    ledger = ReceiptLedger(args.ledger)
    receipt = ledger.append(decision)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if decision.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
