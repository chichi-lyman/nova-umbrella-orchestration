"""Synthetic-data evidence ledger prototype; standard-library core."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class LedgerError(Exception):
    """Base class for expected domain errors."""


class AuthorizationError(LedgerError):
    pass


class NotFoundError(LedgerError):
    pass


class ConflictError(LedgerError):
    pass


class ValidationError(LedgerError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Actor:
    actor_id: str
    role: str


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    case_ref: str
    description: str
    category: str
    intake_source: str
    custodian_id: str
    state: str
    created_at: str
    digital_sha256: Optional[str] = None


class EvidenceLedger:
    """SQLite-backed service. Authentication is expected to be supplied externally."""

    CUSTODY_ROLES = {"evidence_technician", "custodian", "admin"}
    REVIEW_ROLES = {"evidence_technician", "custodian", "analyst", "admin"}

    def __init__(self, database: str | Path = ":memory:") -> None:
        self.database = str(database)
        self._connection = sqlite3.connect(self.database, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        self._connection.close()

    def _initialize(self) -> None:
        with self._connection:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id TEXT PRIMARY KEY,
                    case_ref TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    intake_source TEXT NOT NULL,
                    custodian_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    digital_sha256 TEXT
                );
                CREATE TABLE IF NOT EXISTS custody_events (
                    event_id TEXT PRIMARY KEY,
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    from_custodian TEXT,
                    to_custodian TEXT,
                    transfer_id TEXT,
                    note TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id TEXT PRIMARY KEY,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS transfers (
                    transfer_id TEXT PRIMARY KEY,
                    evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id),
                    from_custodian TEXT NOT NULL,
                    to_custodian TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS custody_events_no_update
                BEFORE UPDATE ON custody_events
                BEGIN
                    SELECT RAISE(ABORT, 'custody events are append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS custody_events_no_delete
                BEFORE DELETE ON custody_events
                BEGIN
                    SELECT RAISE(ABORT, 'custody events are append-only');
                END;
            """)

    def _audit(self, actor: Actor, action: str, resource_id: str,
               outcome: str, reason: str = "") -> None:
        self._connection.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), actor.actor_id, action, resource_id,
             outcome, utc_now(), reason[:500]),
        )

    def _require_role(self, actor: Actor, allowed: set[str]) -> None:
        if not actor.actor_id.strip() or actor.role not in allowed:
            raise AuthorizationError("Actor is not authorized for this operation.")

    def _get_item(self, evidence_id: str) -> EvidenceItem:
        row = self._connection.execute(
            "SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError("Evidence item not found.")
        return EvidenceItem(**dict(row))

    def register_evidence(
        self, actor: Actor, *, case_ref: str, description: str,
        category: str, intake_source: str, evidence_id: Optional[str] = None,
        digital_bytes: Optional[bytes] = None,
    ) -> EvidenceItem:
        resource_id = evidence_id or "unassigned"
        try:
            self._require_role(actor, self.CUSTODY_ROLES)
            values = [case_ref, description, category, intake_source]
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValidationError("case_ref, description, category, and intake_source are required.")
            evidence_id = evidence_id or f"EV-{uuid.uuid4().hex[:12].upper()}"
            digest = hashlib.sha256(digital_bytes).hexdigest() if digital_bytes is not None else None
            created = utc_now()
            with self._connection:
                self._connection.execute(
                    "INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (evidence_id, case_ref, description, category, intake_source,
                     actor.actor_id, "IN_CUSTODY", created, digest),
                )
                self._connection.execute(
                    "INSERT INTO custody_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), evidence_id, "REGISTERED", actor.actor_id,
                     created, None, actor.actor_id, None, "Initial intake"),
                )
                self._audit(actor, "REGISTER_EVIDENCE", evidence_id, "ALLOW")
            return self._get_item(evidence_id)
        except Exception as exc:
            with self._connection:
                self._audit(actor, "REGISTER_EVIDENCE", resource_id, "DENY", str(exc))
            raise

    def request_transfer(self, actor: Actor, evidence_id: str, recipient_id: str) -> str:
        try:
            self._require_role(actor, self.CUSTODY_ROLES)
            if not recipient_id.strip() or recipient_id == actor.actor_id:
                raise ValidationError("Recipient must be a distinct, non-empty actor ID.")
            item = self._get_item(evidence_id)
            if item.custodian_id != actor.actor_id:
                raise AuthorizationError("Only the current custodian can request a transfer.")
            if item.state != "IN_CUSTODY":
                raise ConflictError("Evidence is not available for transfer.")
            transfer_id = f"TR-{uuid.uuid4().hex[:12].upper()}"
            now = utc_now()
            with self._connection:
                self._connection.execute(
                    "INSERT INTO transfers VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (transfer_id, evidence_id, actor.actor_id, recipient_id,
                     actor.actor_id, now, "PENDING"),
                )
                self._connection.execute(
                    "UPDATE evidence SET state = ? WHERE evidence_id = ?",
                    ("TRANSFER_PENDING", evidence_id),
                )
                self._connection.execute(
                    "INSERT INTO custody_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), evidence_id, "TRANSFER_REQUESTED", actor.actor_id,
                     now, actor.actor_id, recipient_id, transfer_id, ""),
                )
                self._audit(actor, "REQUEST_TRANSFER", evidence_id, "ALLOW")
            return transfer_id
        except Exception as exc:
            with self._connection:
                self._audit(actor, "REQUEST_TRANSFER", evidence_id, "DENY", str(exc))
            raise

    def accept_transfer(self, actor: Actor, transfer_id: str) -> EvidenceItem:
        try:
            self._require_role(actor, self.CUSTODY_ROLES)
            transfer = self._connection.execute(
                "SELECT * FROM transfers WHERE transfer_id = ?", (transfer_id,)
            ).fetchone()
            if transfer is None:
                raise NotFoundError("Transfer not found.")
            if transfer["status"] != "PENDING":
                raise ConflictError("Transfer is not pending.")
            if actor.actor_id != transfer["to_custodian"]:
                raise AuthorizationError("Only the designated receiver can accept this transfer.")
            now = utc_now()
            with self._connection:
                self._connection.execute(
                    "UPDATE transfers SET status = ? WHERE transfer_id = ?",
                    ("ACCEPTED", transfer_id),
                )
                self._connection.execute(
                    "UPDATE evidence SET custodian_id = ?, state = ? WHERE evidence_id = ?",
                    (actor.actor_id, "IN_CUSTODY", transfer["evidence_id"]),
                )
                self._connection.execute(
                    "INSERT INTO custody_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), transfer["evidence_id"], "TRANSFER_ACCEPTED",
                     actor.actor_id, now, transfer["from_custodian"], actor.actor_id,
                     transfer_id, "Receiver acknowledgment"),
                )
                self._audit(actor, "ACCEPT_TRANSFER", transfer["evidence_id"], "ALLOW")
            return self._get_item(transfer["evidence_id"])
        except Exception as exc:
            with self._connection:
                self._audit(actor, "ACCEPT_TRANSFER", transfer_id, "DENY", str(exc))
            raise

    def get_evidence(self, actor: Actor, evidence_id: str) -> EvidenceItem:
        try:
            self._require_role(actor, self.REVIEW_ROLES)
            item = self._get_item(evidence_id)
            with self._connection:
                self._audit(actor, "READ_EVIDENCE", evidence_id, "ALLOW")
            return item
        except Exception as exc:
            with self._connection:
                self._audit(actor, "READ_EVIDENCE", evidence_id, "DENY", str(exc))
            raise

    def custody_history(self, actor: Actor, evidence_id: str) -> list[dict]:
        try:
            self._require_role(actor, self.REVIEW_ROLES)
            self._get_item(evidence_id)
            rows = self._connection.execute(
                "SELECT event_id, evidence_id, event_type, actor_id, event_at, "
                "from_custodian, to_custodian, transfer_id, note "
                "FROM custody_events WHERE evidence_id = ? ORDER BY rowid",
                (evidence_id,),
            ).fetchall()
            with self._connection:
                self._audit(actor, "READ_CUSTODY_HISTORY", evidence_id, "ALLOW")
            return [dict(row) for row in rows]
        except Exception as exc:
            with self._connection:
                self._audit(actor, "READ_CUSTODY_HISTORY", evidence_id, "DENY", str(exc))
            raise

    def verify_digital_integrity(self, actor: Actor, evidence_id: str,
                                 digital_bytes: bytes) -> dict:
        try:
            self._require_role(actor, self.REVIEW_ROLES)
            item = self._get_item(evidence_id)
            if item.digital_sha256 is None:
                raise ValidationError("This item has no recorded digital evidence digest.")
            supplied = hashlib.sha256(digital_bytes).hexdigest()
            result = supplied == item.digital_sha256
            with self._connection:
                self._audit(actor, "VERIFY_DIGITAL_INTEGRITY", evidence_id,
                            "ALLOW" if result else "MISMATCH",
                            "sha256 comparison completed")
            return {"algorithm": "sha256", "expected": item.digital_sha256,
                    "observed": supplied, "matches": result}
        except Exception as exc:
            with self._connection:
                self._audit(actor, "VERIFY_DIGITAL_INTEGRITY", evidence_id, "DENY", str(exc))
            raise

    def audit_history(self, actor: Actor) -> list[dict]:
        self._require_role(actor, {"admin", "auditor"})
        rows = self._connection.execute(
            "SELECT audit_id, actor_id, action, resource_id, outcome, occurred_at, reason "
            "FROM audit_events ORDER BY rowid"
        ).fetchall()
        return [dict(row) for row in rows]

    def export_json(self, actor: Actor, evidence_id: str) -> dict:
        item = self.get_evidence(actor, evidence_id)
        events = self.custody_history(actor, evidence_id)
        return {"evidence": item.__dict__, "custody_events": events}
