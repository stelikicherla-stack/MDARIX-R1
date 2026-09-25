"""Run provider-contract, cost-reconciliation, and concurrent safety checks."""
import argparse
import sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from genai.provider import GenAIProvider
from genai.validation import reconcile_cost, validate_contract, validate_multi_instance

parser = argparse.ArgumentParser()
parser.add_argument("--invoice-total", type=Decimal)
args = parser.parse_args()
provider = GenAIProvider()
contract = validate_contract(provider)
print({"contract": contract.status, "checks": contract.checks, "limitations": contract.limitations})
print({"multi_instance": validate_multi_instance(provider=provider)})
if args.invoice_total is not None:
    print({"cost_reconciliation": reconcile_cost(executions=[], provider_invoice_total=args.invoice_total)})
