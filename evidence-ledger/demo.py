"""Run a synthetic custody lifecycle walkthrough."""
import json

from evidence_ledger import Actor, EvidenceLedger

ledger = EvidenceLedger()
technician = Actor("demo-tech-01", "evidence_technician")
receiver = Actor("demo-custodian-02", "custodian")
auditor = Actor("demo-auditor", "auditor")

item = ledger.register_evidence(
    technician,
    case_ref="SYN-CASE-2026-001",
    description="Fictional sealed training package",
    category="packaged_item",
    intake_source="Synthetic portfolio scenario",
    evidence_id="EV-SYN-2026-001",
    digital_bytes=b"fictional sample file bytes",
)
transfer = ledger.request_transfer(technician, item.evidence_id, receiver.actor_id)
received = ledger.accept_transfer(receiver, transfer)

print("Evidence after acknowledged transfer:")
print(json.dumps(received.__dict__, indent=2))
print("\nCustody event history:")
print(json.dumps(ledger.custody_history(auditor, item.evidence_id), indent=2))
print("\nAudit records:")
print(json.dumps(ledger.audit_history(auditor), indent=2))
ledger.close()
