# backend/app/models.py
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey, Enum, Text, Boolean, Table
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


# Enums
class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    SETTLED = "settled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Association table for session participants
session_participants = Table(
    'session_participants',
    Base.metadata,
    Column('session_id', Integer, ForeignKey('sessions.id', ondelete="CASCADE")),
    Column('participant_id', Integer, ForeignKey('participants.id', ondelete="CASCADE"))
)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(6), unique=True, index=True, nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    locked_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)

    # Venue info (optional)
    venue_name = Column(String(255), nullable=True)
    currency = Column(String(3), default="USD")

    # Totals
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    tip_percent = Column(Float, default=18.0)
    tip_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)

    # Relationships
    items = relationship("Item", back_populates="session", cascade="all, delete-orphan")
    participants = relationship("Participant", secondary=session_participants, back_populates="sessions")
    transactions = relationship("Transaction", back_populates="session", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    color = Column(String(7), default="#2196F3")  # Hex color for UI
    payment_handle = Column(String(100), nullable=True)  # venmo: @username

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", secondary=session_participants, back_populates="participants")
    assignments = relationship("Assignment", back_populates="participant", cascade="all, delete-orphan")
    payments_made = relationship("Transaction", foreign_keys="Transaction.payer_id", back_populates="payer")
    payments_received = relationship("Transaction", foreign_keys="Transaction.payee_id", back_populates="payee")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)

    # Item details
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=True)  # Calculated if quantity > 1

    # OCR metadata
    ocr_confidence = Column(Float, nullable=True)  # 0-100
    raw_ocr_text = Column(Text, nullable=True)

    # Status
    is_disputed = Column(Boolean, default=False)
    dispute_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="items")
    assignments = relationship("Assignment", back_populates="item", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)

    # Split details
    share_percent = Column(Float, default=100.0)  # 100 = full, 50 = half, etc.
    fixed_amount = Column(Float, nullable=True)  # Override percentage

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    item = relationship("Item", back_populates="assignments")
    participant = relationship("Participant", back_populates="assignments")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    payer_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)
    payee_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), nullable=False)

    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Payment method tracking
    method = Column(String(50), default="pending")  # venmo, cashapp, apple_pay, etc.
    external_id = Column(String(255), nullable=True)  # Payment provider reference

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="transactions")
    payer = relationship("Participant", foreign_keys=[payer_id], back_populates="payments_made")
    payee = relationship("Participant", foreign_keys=[payee_id], back_populates="payments_received")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="SET NULL"), nullable=True)

    action = Column(String(50), nullable=False)  # item_added, item_assigned, session_locked, etc.
    details = Column(Text, nullable=True)  # JSON string of changes

    created_at = Column(DateTime, default=datetime.utcnow)
