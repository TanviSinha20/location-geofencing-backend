"""Business logic for Digital ID issuance and verification."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.digital_id import TouristDigitalID
from app.models.chain_block import ChainBlock
from app.identity.chain import append_block, compute_block_hash, format_timestamp
from app.utils.exceptions import ValidationError


def issue_id(tourist_id: str, kyc_hash: str, valid_until: datetime, db: Session) -> TouristDigitalID:
    """
    Issue a new digital ID for a tourist, deactivate any existing ID,
    and anchor the registration event to the blockchain ledger.
    """
    # 1. Check for existing ID
    existing = db.scalar(
        select(TouristDigitalID).where(TouristDigitalID.tourist_id == tourist_id)
    )

    did_uri = f"did:sih:tourist:{tourist_id}"

    if existing:
        existing.kyc_hash = kyc_hash
        existing.valid_until = valid_until
        existing.is_active = True
        digital_id = existing
    else:
        digital_id = TouristDigitalID(
            tourist_id=tourist_id,
            did=did_uri,
            kyc_hash=kyc_hash,
            valid_until=valid_until,
            is_active=True
        )
        db.add(digital_id)

    db.flush()

    # 2. Anchor registration on-chain
    anchor_data = {
        "event_type": "DID_ISSUED",
        "tourist_id": tourist_id,
        "did": did_uri,
        "kyc_hash": kyc_hash,
        "valid_until": valid_until.isoformat()
    }
    append_block(anchor_data, db)

    db.commit()
    db.refresh(digital_id)
    return digital_id


def verify_chain(db: Session) -> tuple[bool, int, str]:
    """
    Verify the cryptographic integrity of the blockchain ledger.
    Returns: (is_valid, blocks_count, status_message)
    """
    blocks = db.scalars(
        select(ChainBlock).order_by(ChainBlock.block_index)
    ).all()

    if not blocks:
        return True, 0, "Blockchain ledger is empty (valid)."

    # Verify Genesis block
    genesis = blocks[0]
    if genesis.block_index != 0:
        return False, len(blocks), f"Integrity failed: block at index 0 is not Genesis (has index {genesis.block_index})."

    # Recompute Genesis hash
    # Ensure timezone handling is matched (stored as UTC/isoformat in compute_block_hash)
    genesis_time_str = format_timestamp(genesis.timestamp)
    expected_genesis_hash = compute_block_hash(
        0, genesis_time_str, genesis.data, genesis.previous_hash
    )
    if genesis.hash != expected_genesis_hash:
        return False, len(blocks), f"Integrity failed: Genesis block hash is corrupted or tampered."

    # Verify subsequent blocks
    for i in range(1, len(blocks)):
        prev = blocks[i - 1]
        curr = blocks[i]

        # 1. Index sequence check
        if curr.block_index != prev.block_index + 1:
            return False, len(blocks), f"Integrity failed: sequence gap between index {prev.block_index} and {curr.block_index}."

        # 2. Previous hash link check
        if curr.previous_hash != prev.hash:
            return False, len(blocks), f"Integrity failed: block {curr.block_index} previous_hash does not match parent hash."

        # 3. Hash verification
        curr_time_str = format_timestamp(curr.timestamp)
        expected_hash = compute_block_hash(
            curr.block_index, curr_time_str, curr.data, curr.previous_hash
        )
        if curr.hash != expected_hash:
            return False, len(blocks), f"Integrity failed: block {curr.block_index} hash value is tampered."

    return True, len(blocks), f"Blockchain validation successful. Integrity verified for all {len(blocks)} blocks."
