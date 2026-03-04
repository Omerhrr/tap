# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


# Enums
class SessionStatus(str, Enum):
    active = "active"
    locked = "locked"
    settled = "settled"


class PaymentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


# Participant schemas
class ParticipantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = Field(default="#2196F3", pattern=r"^#[0-9A-Fa-f]{6}$")
    payment_handle: Optional[str] = None


class ParticipantCreate(ParticipantBase):
    device_id: str


class ParticipantResponse(ParticipantBase):
    id: int
    device_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Item schemas
class ItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=1)


class ItemCreate(ItemBase):
    ocr_confidence: Optional[float] = None
    raw_ocr_text: Optional[str] = None


class ItemResponse(ItemBase):
    id: int
    session_id: int
    ocr_confidence: Optional[float] = None
    is_disputed: bool
    dispute_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Assignment schemas
class AssignmentBase(BaseModel):
    participant_id: int
    share_percent: float = Field(default=100.0, gt=0, le=100)
    fixed_amount: Optional[float] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentResponse(AssignmentBase):
    id: int
    item_id: int
    participant: ParticipantResponse

    class Config:
        from_attributes = True


# Item with assignments
class ItemWithAssignments(ItemResponse):
    assignments: List[AssignmentResponse] = []
    unassigned_amount: float = 0.0


# Session schemas
class SessionBase(BaseModel):
    venue_name: Optional[str] = None
    currency: str = "USD"
    tip_percent: float = 18.0


class SessionCreate(BaseModel):
    pass  # Server generates code


class SessionResponse(BaseModel):
    id: int
    code: str
    status: SessionStatus
    created_at: datetime
    venue_name: Optional[str]
    currency: str
    subtotal: float
    tax_amount: float
    tip_percent: float
    tip_amount: float
    total_amount: float

    class Config:
        from_attributes = True


# Full session with nested data
class SessionDetail(SessionResponse):
    participants: List[ParticipantResponse] = []
    items: List[ItemWithAssignments] = []

    # Calculated shares per participant
    participant_shares: Dict[int, float] = {}


# OCR schemas
class OCRItem(BaseModel):
    description: str
    amount: float
    quantity: int = 1
    confidence: Optional[float] = None


class OCRResponse(BaseModel):
    items: List[OCRItem]
    raw_text: Optional[str] = None
    success: bool
    error_message: Optional[str] = None


# WebSocket messages
class WSMessageType(str, Enum):
    participant_joined = "participant_joined"
    participant_left = "participant_left"
    item_added = "item_added"
    item_updated = "item_updated"
    item_removed = "item_removed"
    item_assigned = "item_assigned"
    assignment_removed = "assignment_removed"
    item_disputed = "item_disputed"
    session_locked = "session_locked"
    session_settled = "session_settled"
    state_sync = "state_sync"
    ping = "ping"
    pong = "pong"


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_device_id: Optional[str] = None


# Transaction schemas
class TransactionCreate(BaseModel):
    payer_id: int
    payee_id: int
    amount: float


class TransactionResponse(TransactionCreate):
    id: int
    session_id: int
    status: PaymentStatus
    method: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Session update schemas
class SessionUpdate(BaseModel):
    venue_name: Optional[str] = None
    tax_amount: Optional[float] = None
    tip_percent: Optional[float] = None


class ItemUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    quantity: Optional[int] = None


class DisputeRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=255)


class AutoAssignRequest(BaseModel):
    pass
