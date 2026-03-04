# backend/app/routers/sessions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Session, SessionStatus
from app.schemas import (
    SessionCreate, SessionResponse, SessionDetail,
    ParticipantCreate, ParticipantResponse,
    SessionUpdate
)
from app import crud
from app.services.calculation import calculate_shares, calculate_settlement
from app.websocket import broadcast_to_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    db: AsyncSession = Depends(get_db)
):
    """Create a new bill-splitting session"""
    session = await crud.create_session(db)
    return session


@router.get("/{code}", response_model=SessionDetail)
async def get_session(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get session details by code"""
    session = await crud.get_session_by_code(db, code)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with code '{code}' not found"
        )

    # Calculate shares
    shares = calculate_shares(session)

    return SessionDetail(
        **{c.name: getattr(session, c.name) for c in session.__table__.columns},
        participants=session.participants,
        items=session.items,
        participant_shares=shares
    )


@router.post("/{session_id}/join", response_model=ParticipantResponse, status_code=status.HTTP_200_OK)
async def join_session(
    session_id: int,
    participant_data: ParticipantCreate,
    db: AsyncSession = Depends(get_db)
):
    """Join an existing session"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join a locked or settled session"
        )

    # Create or get participant
    participant = await crud.create_participant(db, participant_data)

    # Add to session
    await crud.add_participant_to_session(db, session, participant)

    # Broadcast to other participants
    await broadcast_to_session(
        session.id,
        {
            "type": "participant_joined",
            "data": {
                "id": participant.id,
                "name": participant.name,
                "color": participant.color
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(
        db, session.id, "participant_joined",
        participant.id, f"Participant '{participant.name}' joined"
    )

    return participant


@router.post("/{session_id}/lock", response_model=SessionResponse)
async def lock_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Lock session for payment settlement"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active"
        )

    session = await crud.lock_session(db, session)

    # Calculate final shares
    shares = calculate_shares(session)

    # Broadcast lock event
    await broadcast_to_session(
        session.id,
        {
            "type": "session_locked",
            "data": {
                "locked_at": session.locked_at.isoformat(),
                "final_shares": shares
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(db, session.id, "session_locked")

    return session


@router.post("/{session_id}/settle", response_model=SessionResponse)
async def settle_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark session as settled"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session must be locked before settling"
        )

    session = await crud.settle_session(db, session)

    # Create settlement transactions
    shares = calculate_shares(session)
    transactions = calculate_settlement(shares)

    for tx in transactions:
        await crud.create_transaction(db, session, tx)

    # Broadcast settle event
    await broadcast_to_session(
        session.id,
        {
            "type": "session_settled",
            "data": {
                "settled_at": session.settled_at.isoformat()
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(db, session.id, "session_settled")

    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    update_data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update session details (venue, tax, tip)"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update locked or settled session"
        )

    # Update fields
    if update_data.venue_name is not None:
        session.venue_name = update_data.venue_name
    if update_data.tax_amount is not None:
        session.tax_amount = update_data.tax_amount
    if update_data.tip_percent is not None:
        session.tip_percent = update_data.tip_percent

    await db.commit()

    # Recalculate totals
    session = await crud.update_session_totals(db, session)

    return session


@router.post("/{session_id}/auto-assign", response_model=SessionDetail)
async def auto_assign_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Automatically assign all items equally among participants"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify locked or settled session"
        )

    if not session.participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No participants in session"
        )

    session = await crud.auto_assign_items(db, session)

    # Calculate shares
    shares = calculate_shares(session)

    # Broadcast state sync
    await broadcast_to_session(
        session.id,
        {
            "type": "state_sync",
            "data": {
                "items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "amount": item.amount,
                        "assignments": [
                            {
                                "id": a.id,
                                "participant_id": a.participant_id,
                                "share_percent": a.share_percent
                            }
                            for a in item.assignments
                        ]
                    }
                    for item in session.items
                ]
            }
        }
    )

    return SessionDetail(
        **{c.name: getattr(session, c.name) for c in session.__table__.columns},
        participants=session.participants,
        items=session.items,
        participant_shares=shares
    )
