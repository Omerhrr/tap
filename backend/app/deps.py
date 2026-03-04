# backend/app/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Session, Participant, SessionStatus


async def get_session_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
) -> Session:
    """Get session by code or raise 404"""
    result = await db.execute(
        select(Session).where(Session.code == code)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with code '{code}' not found"
        )

    return session


async def get_session_by_id(
    session_id: int,
    db: AsyncSession = Depends(get_db)
) -> Session:
    """Get session by ID or raise 404"""
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID {session_id} not found"
        )

    return session


async def get_participant_by_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
) -> Optional[Participant]:
    """Get participant by device ID"""
    result = await db.execute(
        select(Participant).where(Participant.device_id == device_id)
    )
    return result.scalar_one_or_none()


def check_session_active(session: Session) -> None:
    """Check if session is still active for modifications"""
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is {session.status.value}. Cannot modify."
        )


def check_session_locked(session: Session) -> None:
    """Check if session is locked for settlement"""
    if session.status != SessionStatus.LOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session must be locked before settling"
        )
