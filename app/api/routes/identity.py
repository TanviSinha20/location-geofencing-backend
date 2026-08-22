"""Digital ID and Audit Ledger API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import APIResponse
from app.schemas.identity import (
    DigitalIDIssueRequest,
    DigitalIDResponse,
    BlockResponse,
    ChainVerifyResponse,
)
from app.models.digital_id import TouristDigitalID
from app.models.chain_block import ChainBlock
from app.identity.did_service import issue_id, verify_chain
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/identity", tags=["identity"])


@router.post(
    "/issue",
    response_model=APIResponse[DigitalIDResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Issue or update tourist digital identity (DID) and anchor registration on-chain",
)
def issue_digital_id(
    payload: DigitalIDIssueRequest,
    db: Session = Depends(get_db)
) -> APIResponse[DigitalIDResponse]:
    digital_id = issue_id(
        tourist_id=payload.tourist_id,
        kyc_hash=payload.kyc_hash,
        valid_until=payload.valid_until,
        db=db
    )
    response_data = DigitalIDResponse.model_validate(digital_id)
    return APIResponse(
        data=response_data,
        message="Tourist digital identity successfully generated and anchored to audit ledger"
    )


@router.get(
    "/verify/{tourist_id}",
    response_model=APIResponse[DigitalIDResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve and verify the status of a tourist's digital ID",
)
def verify_tourist_id(
    tourist_id: str,
    db: Session = Depends(get_db)
) -> APIResponse[DigitalIDResponse]:
    digital_id = db.scalar(
        select(TouristDigitalID).where(TouristDigitalID.tourist_id == tourist_id)
    )
    if not digital_id:
        raise NotFoundError(f"No digital identity (DID) registered for tourist '{tourist_id}'")

    response_data = DigitalIDResponse.model_validate(digital_id)
    return APIResponse(
        data=response_data,
        message="Tourist digital identity status verified"
    )


@router.get(
    "/chain",
    response_model=APIResponse[list[BlockResponse]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all blocks on the audit trail blockchain ledger",
)
def get_audit_trail_chain(db: Session = Depends(get_db)) -> APIResponse[list[BlockResponse]]:
    blocks = db.scalars(
        select(ChainBlock).order_by(ChainBlock.block_index)
    ).all()

    # Verify chain integrity
    is_valid, count, status_message = verify_chain(db)

    serialized_blocks = [BlockResponse.model_validate(b) for b in blocks]
    return APIResponse(
        data=serialized_blocks,
        message=f"Blockchain validation status: {status_message}"
    )


@router.get(
    "/chain/verify",
    response_model=APIResponse[ChainVerifyResponse],
    status_code=status.HTTP_200_OK,
    summary="Cryptographically verify the integrity of the audit blockchain",
)
def verify_audit_blockchain(db: Session = Depends(get_db)) -> APIResponse[ChainVerifyResponse]:
    is_valid, count, status_message = verify_chain(db)
    response_data = ChainVerifyResponse(
        is_valid=is_valid,
        blocks_count=count,
        verification_message=status_message
    )
    return APIResponse(
        data=response_data,
        message="Audit blockchain verification check completed"
    )
