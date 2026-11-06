"""Optional FastAPI adapter. Demo headers are not production authentication."""
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from evidence_ledger import (
    Actor, AuthorizationError, ConflictError, EvidenceLedger, LedgerError,
    NotFoundError, ValidationError,
)

app = FastAPI(
    title="CRJS 355 Evidence Ledger (Portfolio Prototype)",
    version="0.1.0",
    description="Synthetic-data demonstration only; not a certified forensic system.",
)
ledger = EvidenceLedger("evidence_ledger.sqlite3")


class IntakeRequest(BaseModel):
    case_ref: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    category: str = Field(min_length=1, max_length=100)
    intake_source: str = Field(min_length=1, max_length=200)
    evidence_id: str | None = Field(default=None, max_length=100)
    digital_text_payload: str | None = None


class TransferRequest(BaseModel):
    recipient_id: str = Field(min_length=1, max_length=100)


def actor_from_headers(actor_id: str | None, actor_role: str | None) -> Actor:
    if not actor_id or not actor_role:
        raise HTTPException(status_code=401, detail="Demo actor headers required.")
    return Actor(actor_id, actor_role)


def handle_error(exc: Exception) -> None:
    if isinstance(exc, AuthorizationError):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, LedgerError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(status_code=500, detail="Unexpected internal error.")


@app.post("/evidence", status_code=201)
def register_evidence(
    request: IntakeRequest,
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        item = ledger.register_evidence(
            actor, case_ref=request.case_ref, description=request.description,
            category=request.category, intake_source=request.intake_source,
            evidence_id=request.evidence_id,
            digital_bytes=request.digital_text_payload.encode() if request.digital_text_payload else None,
        )
        return item.__dict__
    except Exception as exc:
        handle_error(exc)


@app.get("/evidence/{evidence_id}")
def get_evidence(
    evidence_id: str,
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        return ledger.get_evidence(actor, evidence_id).__dict__
    except Exception as exc:
        handle_error(exc)


@app.get("/evidence/{evidence_id}/custody")
def custody_history(
    evidence_id: str,
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        return ledger.custody_history(actor, evidence_id)
    except Exception as exc:
        handle_error(exc)


@app.post("/evidence/{evidence_id}/transfers", status_code=201)
def request_transfer(
    evidence_id: str,
    request: TransferRequest,
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        return {"transfer_id": ledger.request_transfer(actor, evidence_id, request.recipient_id)}
    except Exception as exc:
        handle_error(exc)


@app.post("/transfers/{transfer_id}/accept")
def accept_transfer(
    transfer_id: str,
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        return ledger.accept_transfer(actor, transfer_id).__dict__
    except Exception as exc:
        handle_error(exc)


@app.get("/audit")
def audit_history(
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
):
    actor = actor_from_headers(x_actor_id, x_actor_role)
    try:
        return ledger.audit_history(actor)
    except Exception as exc:
        handle_error(exc)
