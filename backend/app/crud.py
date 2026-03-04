# backend/app/crud.py
import random
import string
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models import (
    Session, Participant, Item, Assignment, Transaction,
    AuditLog, SessionStatus, PaymentStatus
)
from app.schemas import (
    SessionCreate, ParticipantCreate, ItemCreate,
    AssignmentCreate, TransactionCreate
)


def generate_session_code(length: int = 6) -> str:
    """Generate a unique session code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


# Session CRUD
async def create_session(db: AsyncSession, session_data: SessionCreate = None) -> Session:
    """Create a new session with a unique code"""
    # Generate unique code
    code = generate_session_code()
    while await get_session_by_code(db, code):
        code = generate_session_code()

    session = Session(code=code)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session_by_code(db: AsyncSession, code: str) -> Optional[Session]:
    """Get session by code with all relationships"""
    result = await db.execute(
        select(Session)
        .where(Session.code == code)
        .options(
            selectinload(Session.participants),
            selectinload(Session.items).selectinload(Item.assignments).selectinload(Assignment.participant)
        )
    )
    return result.scalar_one_or_none()


async def get_session_by_id(db: AsyncSession, session_id: int) -> Optional[Session]:
    """Get session by ID with all relationships"""
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
        .options(
            selectinload(Session.participants),
            selectinload(Session.items).selectinload(Item.assignments).selectinload(Assignment.participant)
        )
    )
    return result.scalar_one_or_none()


async def update_session_totals(db: AsyncSession, session: Session) -> Session:
    """Recalculate session totals"""
    # Calculate subtotal from items
    subtotal = sum(item.amount for item in session.items)

    # Calculate tip
    tip_amount = round(subtotal * (session.tip_percent / 100), 2)

    # Update session
    session.subtotal = subtotal
    session.tip_amount = tip_amount
    session.total_amount = subtotal + session.tax_amount + tip_amount

    await db.commit()
    await db.refresh(session)
    return session


async def lock_session(db: AsyncSession, session: Session) -> Session:
    """Lock session for payment settlement"""
    from datetime import datetime
    session.status = SessionStatus.LOCKED
    session.locked_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


async def settle_session(db: AsyncSession, session: Session) -> Session:
    """Mark session as settled"""
    from datetime import datetime
    session.status = SessionStatus.SETTLED
    session.settled_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)
    return session


# Participant CRUD
async def create_participant(db: AsyncSession, participant_data: ParticipantCreate) -> Participant:
    """Create or get existing participant by device_id"""
    # Check if participant exists
    result = await db.execute(
        select(Participant).where(Participant.device_id == participant_data.device_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update name if provided
        if participant_data.name:
            existing.name = participant_data.name
        if participant_data.color:
            existing.color = participant_data.color
        await db.commit()
        await db.refresh(existing)
        return existing

    participant = Participant(
        device_id=participant_data.device_id,
        name=participant_data.name,
        color=participant_data.color or "#2196F3",
        payment_handle=participant_data.payment_handle
    )
    db.add(participant)
    await db.commit()
    await db.refresh(participant)
    return participant


async def add_participant_to_session(
    db: AsyncSession,
    session: Session,
    participant: Participant
) -> Participant:
    """Add participant to session if not already in it"""
    if participant not in session.participants:
        session.participants.append(participant)
        await db.commit()

    # Refresh to get updated relationships
    await db.refresh(session, ["participants"])
    return participant


async def get_participant(db: AsyncSession, participant_id: int) -> Optional[Participant]:
    """Get participant by ID"""
    result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    return result.scalar_one_or_none()


# Item CRUD
async def create_item(
    db: AsyncSession,
    session: Session,
    item_data: ItemCreate
) -> Item:
    """Create a new item in session"""
    item = Item(
        session_id=session.id,
        description=item_data.description,
        amount=item_data.amount,
        quantity=item_data.quantity,
        unit_price=item_data.amount / item_data.quantity if item_data.quantity > 1 else item_data.amount,
        ocr_confidence=item_data.ocr_confidence,
        raw_ocr_text=item_data.raw_ocr_text
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    # Update session totals
    await update_session_totals(db, session)

    return item


async def create_items_bulk(
    db: AsyncSession,
    session: Session,
    items_data: List[ItemCreate]
) -> List[Item]:
    """Create multiple items at once (from OCR)"""
    items = []
    for item_data in items_data:
        item = Item(
            session_id=session.id,
            description=item_data.description,
            amount=item_data.amount,
            quantity=item_data.quantity,
            unit_price=item_data.amount / item_data.quantity if item_data.quantity > 1 else item_data.amount,
            ocr_confidence=item_data.ocr_confidence,
            raw_ocr_text=item_data.raw_ocr_text
        )
        items.append(item)
        db.add(item)

    await db.commit()

    for item in items:
        await db.refresh(item)

    # Update session totals
    await update_session_totals(db, session)

    return items


async def update_item(
    db: AsyncSession,
    item: Item,
    description: str = None,
    amount: float = None,
    quantity: int = None
) -> Item:
    """Update item details"""
    if description is not None:
        item.description = description
    if amount is not None:
        item.amount = amount
    if quantity is not None:
        item.quantity = quantity

    await db.commit()
    await db.refresh(item)

    # Update session totals
    session = await get_session_by_id(db, item.session_id)
    await update_session_totals(db, session)

    return item


async def delete_item(db: AsyncSession, item: Item) -> None:
    """Delete an item"""
    session_id = item.session_id
    await db.delete(item)
    await db.commit()

    # Update session totals
    session = await get_session_by_id(db, session_id)
    await update_session_totals(db, session)


async def dispute_item(
    db: AsyncSession,
    item: Item,
    reason: str
) -> Item:
    """Flag item as disputed"""
    item.is_disputed = True
    item.dispute_reason = reason
    await db.commit()
    await db.refresh(item)
    return item


# Assignment CRUD
async def create_assignment(
    db: AsyncSession,
    item: Item,
    assignment_data: AssignmentCreate
) -> Assignment:
    """Assign an item to a participant"""
    assignment = Assignment(
        item_id=item.id,
        participant_id=assignment_data.participant_id,
        share_percent=assignment_data.share_percent,
        fixed_amount=assignment_data.fixed_amount
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment, ["participant"])
    return assignment


async def delete_assignment(db: AsyncSession, assignment: Assignment) -> None:
    """Remove an assignment"""
    await db.delete(assignment)
    await db.commit()


async def get_assignment(db: AsyncSession, assignment_id: int) -> Optional[Assignment]:
    """Get assignment by ID"""
    result = await db.execute(
        select(Assignment).where(Assignment.id == assignment_id)
    )
    return result.scalar_one_or_none()


# Transaction CRUD
async def create_transaction(
    db: AsyncSession,
    session: Session,
    transaction_data: TransactionCreate
) -> Transaction:
    """Create a transaction record"""
    transaction = Transaction(
        session_id=session.id,
        payer_id=transaction_data.payer_id,
        payee_id=transaction_data.payee_id,
        amount=transaction_data.amount
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_session_transactions(db: AsyncSession, session_id: int) -> List[Transaction]:
    """Get all transactions for a session"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.session_id == session_id)
        .options(selectinload(Transaction.payer), selectinload(Transaction.payee))
    )
    return result.scalars().all()


# Audit Log
async def create_audit_log(
    db: AsyncSession,
    session_id: int,
    action: str,
    participant_id: int = None,
    details: str = None
) -> AuditLog:
    """Create an audit log entry"""
    audit = AuditLog(
        session_id=session_id,
        participant_id=participant_id,
        action=action,
        details=details
    )
    db.add(audit)
    await db.commit()
    return audit


# Auto-assign items equally
async def auto_assign_items(db: AsyncSession, session: Session) -> Session:
    """Automatically assign all items equally among participants"""
    if not session.participants:
        return session

    # Clear existing assignments
    for item in session.items:
        await db.execute(
            delete(Assignment).where(Assignment.item_id == item.id)
        )

    await db.commit()

    # Create equal split assignments
    share_percent = 100.0 / len(session.participants)
    for item in session.items:
        for participant in session.participants:
            assignment = Assignment(
                item_id=item.id,
                participant_id=participant.id,
                share_percent=share_percent
            )
            db.add(assignment)

    await db.commit()

    # Refresh session
    return await get_session_by_id(db, session.id)
