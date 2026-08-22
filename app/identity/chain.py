"""Simulated permissioned blockchain ledger core."""

import hashlib
import json
from datetime import UTC, datetime
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.chain_block import ChainBlock


def format_timestamp(dt: datetime) -> str:
    """Format a datetime deterministically to naive UTC isoformat."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt.isoformat()


def compute_block_hash(index: int, timestamp_str: str, data_str: str, previous_hash: str) -> str:
    """Compute the SHA-256 hash of block contents deterministically."""
    block_string = f"{index}:{timestamp_str}:{data_str}:{previous_hash}"
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


def append_block(data: dict, db: Session) -> ChainBlock:
    """
    Append a new block containing a data payload to the ledger.
    Creates a genesis block if the chain is empty.
    """
    # 1. Fetch latest block
    latest_block = db.scalar(
        select(ChainBlock)
        .order_by(desc(ChainBlock.block_index))
        .limit(1)
    )

    # 2. If no latest block exists, create a Genesis block first
    if not latest_block:
        genesis_data = {"message": "Genesis Block - Smart Tourist Safety Audit Trail"}
        genesis_data_str = json.dumps(genesis_data, sort_keys=True)
        genesis_time = datetime.now(UTC)
        genesis_time_str = format_timestamp(genesis_time)
        genesis_hash = compute_block_hash(0, genesis_time_str, genesis_data_str, "0")

        genesis_block = ChainBlock(
            block_index=0,
            timestamp=genesis_time,
            data=genesis_data_str,
            previous_hash="0",
            hash=genesis_hash
        )
        db.add(genesis_block)
        db.commit()
        db.refresh(genesis_block)
        latest_block = genesis_block

    # 3. Create new block
    new_index = latest_block.block_index + 1
    new_time = datetime.now(UTC)
    new_time_str = format_timestamp(new_time)
    data_str = json.dumps(data, sort_keys=True)
    new_hash = compute_block_hash(new_index, new_time_str, data_str, latest_block.hash)

    block = ChainBlock(
        block_index=new_index,
        timestamp=new_time,
        data=data_str,
        previous_hash=latest_block.hash,
        hash=new_hash
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block
