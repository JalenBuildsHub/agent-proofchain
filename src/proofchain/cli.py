"""Command-line interface for portable admission decisions and ledger verification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .admission import AdmissionRequest, evaluate
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
    args = parser.parse_args()

    ledger = ReceiptLedger(args.ledger)
    if args.command == "verify":
        result = ledger.verify()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["valid"] else 1

    policy = AdmissionPolicy.from_json(args.policy)
    request = AdmissionRequest.from_dict(json.loads(Path(args.request).read_text(encoding="utf-8")))
    decision = evaluate(request, policy)
    receipt = ledger.append(decision)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if decision.allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())

