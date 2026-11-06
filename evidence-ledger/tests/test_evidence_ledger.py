import hashlib
import unittest

from evidence_ledger import (
    Actor, AuthorizationError, ConflictError, EvidenceLedger, NotFoundError,
)


class EvidenceLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EvidenceLedger()
        self.tech = Actor("tech-001", "evidence_technician")
        self.receiver = Actor("tech-002", "custodian")
        self.analyst = Actor("analyst-001", "analyst")

    def tearDown(self):
        self.ledger.close()

    def register(self, digital_bytes=None):
        return self.ledger.register_evidence(
            self.tech, case_ref="SYN-CASE-001",
            description="Fictional sealed package", category="packaged_item",
            intake_source="Synthetic training scenario", evidence_id="EV-SYN-001",
            digital_bytes=digital_bytes,
        )

    def test_registration_creates_item_and_initial_event(self):
        item = self.register()
        self.assertEqual(item.state, "IN_CUSTODY")
        self.assertEqual(item.custodian_id, self.tech.actor_id)
        history = self.ledger.custody_history(self.analyst, item.evidence_id)
        self.assertEqual([event["event_type"] for event in history], ["REGISTERED"])

    def test_only_current_custodian_can_request_transfer(self):
        self.register()
        with self.assertRaises(AuthorizationError):
            self.ledger.request_transfer(self.receiver, "EV-SYN-001", "tech-003")

    def test_transfer_requires_recipient_acknowledgment(self):
        self.register()
        transfer_id = self.ledger.request_transfer(self.tech, "EV-SYN-001", "tech-002")
        with self.assertRaises(AuthorizationError):
            self.ledger.accept_transfer(self.tech, transfer_id)
        received = self.ledger.accept_transfer(self.receiver, transfer_id)
        self.assertEqual(received.custodian_id, self.receiver.actor_id)
        self.assertEqual(received.state, "IN_CUSTODY")
        history = self.ledger.custody_history(self.analyst, "EV-SYN-001")
        self.assertEqual([e["event_type"] for e in history],
                         ["REGISTERED", "TRANSFER_REQUESTED", "TRANSFER_ACCEPTED"])

    def test_transfer_cannot_be_accepted_twice(self):
        self.register()
        transfer_id = self.ledger.request_transfer(self.tech, "EV-SYN-001", "tech-002")
        self.ledger.accept_transfer(self.receiver, transfer_id)
        with self.assertRaises(ConflictError):
            self.ledger.accept_transfer(self.receiver, transfer_id)

    def test_duplicate_evidence_id_rejected(self):
        self.register()
        with self.assertRaises(Exception):
            self.register()

    def test_digital_digest_is_recorded_and_verified(self):
        payload = b"synthetic digital evidence bytes"
        item = self.register(payload)
        self.assertEqual(item.digital_sha256, hashlib.sha256(payload).hexdigest())
        result = self.ledger.verify_digital_integrity(self.analyst, item.evidence_id, payload)
        self.assertTrue(result["matches"])
        mismatch = self.ledger.verify_digital_integrity(
            self.analyst, item.evidence_id, b"different synthetic payload"
        )
        self.assertFalse(mismatch["matches"])

    def test_unknown_evidence_returns_not_found(self):
        with self.assertRaises(NotFoundError):
            self.ledger.get_evidence(self.analyst, "missing")

    def test_unauthorized_role_is_rejected(self):
        with self.assertRaises(AuthorizationError):
            self.ledger.register_evidence(
                self.analyst, case_ref="X", description="Y", category="Z",
                intake_source="synthetic"
            )

    def test_audit_records_denied_operations(self):
        self.register()
        with self.assertRaises(AuthorizationError):
            self.ledger.request_transfer(self.receiver, "EV-SYN-001", "tech-003")
        audit = self.ledger.audit_history(Actor("auditor-1", "auditor"))
        self.assertTrue(any(row["action"] == "REQUEST_TRANSFER" and
                            row["outcome"] == "DENY" for row in audit))


if __name__ == "__main__":
    unittest.main()
