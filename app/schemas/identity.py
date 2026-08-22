"""Digital ID and Blockchain response/request schemas."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DigitalIDIssueRequest(BaseModel):
    tourist_id: str = Field(..., min_length=1, max_length=64, description="Unique tourist identifier")
    kyc_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of tourist KYC data")
    valid_until: datetime = Field(..., description="Digital ID expiration timestamp")


class DigitalIDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tourist_id: str
    did: str
    kyc_hash: str
    issued_at: datetime
    valid_until: datetime
    is_active: bool


class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    block_index: int
    timestamp: datetime
    data: dict[str, Any] = Field(..., description="Deserialized JSON block data payload")
    previous_hash: str
    hash: str

    @classmethod
    def model_validate(cls, obj: Any, **kwargs) -> "BlockResponse":
        import json
        if not isinstance(obj, dict):
            # SQLAlchemy model or similar
            data_raw = getattr(obj, "data", "{}")
        else:
            data_raw = obj.get("data", "{}")

        try:
            parsed_data = json.loads(data_raw)
        except Exception:
            parsed_data = {"raw_data": data_raw}

        # Retrieve fields
        if not isinstance(obj, dict):
            return cls(
                block_index=obj.block_index,
                timestamp=obj.timestamp,
                data=parsed_data,
                previous_hash=obj.previous_hash,
                hash=obj.hash
            )
        return cls(
            block_index=obj.get("block_index"),
            timestamp=obj.get("timestamp"),
            data=parsed_data,
            previous_hash=obj.get("previous_hash"),
            hash=obj.get("hash")
        )


class ChainVerifyResponse(BaseModel):
    is_valid: bool = Field(..., description="True if the blockchain integrity is intact")
    blocks_count: int = Field(..., description="Total number of blocks in the chain")
    verification_message: str = Field(..., description="Integrity check validation message details")
