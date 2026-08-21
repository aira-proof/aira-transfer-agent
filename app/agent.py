from __future__ import annotations

import os
from datetime import datetime, timezone

from aira import Aira, AiraError

from .models import Transfer, TransferRequest, TransferStatus

AGENT_ID = "wire-transfer-agent"
AGENT_VERSION = "1.0.0"

_transfers: list[Transfer] = []


def _get_client() -> Aira:
    api_key = os.environ.get("AIRA_API_KEY", "")
    base_url = os.environ.get("AIRA_BASE_URL", "https://api.airaproof.com")
    return Aira(api_key=api_key, base_url=base_url)


def _build_details(req: TransferRequest) -> str:
    return (
        f"Wire transfer of {req.amount_eur:,.2f} {req.currency} "
        f"to {req.recipient} ({req.iban}) in {req.country}. "
        f"Purpose: {req.purpose}"
    )


def process_transfer(req: TransferRequest) -> Transfer:
    aira = _get_client()
    details = _build_details(req)

    transfer = Transfer(request=req, status=TransferStatus.authorized)

    try:
        auth = aira.authorize(
            action_type="wire_transfer",
            details=details,
            agent_id=AGENT_ID,
            agent_version=AGENT_VERSION,
            model_id="transfer-policy-engine",
        )
        transfer.action_uuid = auth.action_uuid

        if auth.status == "pending_approval":
            transfer.status = TransferStatus.pending_approval
            transfer.agent_reasoning = "Transfer held for human approval per policy."
            _transfers.insert(0, transfer)
            return transfer

    except AiraError as e:
        if e.code == "POLICY_DENIED":
            transfer.status = TransferStatus.denied
            transfer.action_uuid = e.details.get("action_uuid") if e.details else None
            transfer.receipt_uuid = e.details.get("receipt_uuid") if e.details else None
            transfer.denial_reason = e.message
            transfer.agent_reasoning = (
                f"Denied by Aira policy: {e.message}"
            )
            if transfer.action_uuid:
                try:
                    verify = aira.verify_action(transfer.action_uuid)
                    transfer.signature = verify.signature
                    transfer.verify_url = (
                        f"https://airaproof.com/verify/{transfer.action_uuid}"
                    )
                except Exception:
                    pass
            _transfers.insert(0, transfer)
            return transfer
        raise

    transfer.status = TransferStatus.executed
    transfer.executed_at = datetime.now(timezone.utc)
    transfer.agent_reasoning = (
        f"Transfer authorized and executed. "
        f"{req.amount_eur:,.2f} {req.currency} sent to {req.recipient}."
    )

    try:
        receipt = aira.notarize(
            action_uuid=auth.action_uuid,
            outcome="completed",
            outcome_details=(
                f"Wire transfer executed: {req.amount_eur:,.2f} {req.currency} "
                f"to {req.recipient} ({req.iban}), country={req.country}"
            ),
        )
        transfer.receipt_uuid = receipt.receipt_uuid
        transfer.signature = receipt.signature
        transfer.verify_url = (
            f"https://airaproof.com/verify/{auth.action_uuid}"
        )
    except AiraError:
        transfer.agent_reasoning += " (notarization failed — receipt unavailable)"

    _transfers.insert(0, transfer)
    return transfer


def get_transfers() -> list[Transfer]:
    return _transfers


def get_transfer(transfer_id: str) -> Transfer | None:
    return next((t for t in _transfers if t.id == transfer_id), None)
