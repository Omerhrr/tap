# backend/app/routers/assignments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Item, Assignment, Session, SessionStatus
from app.schemas import AssignmentCreate, AssignmentResponse
from app import crud
from app.websocket import broadcast_to_session

router = APIRouter(prefix="/items", tags=["assignments"])


@router.post("/{item_id}/assign", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_item(
    item_id: int,
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Assign an item to a participant"""
    item = await db.get(Item, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    session = await crud.get_session_by_id(db, item.session_id)
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign items in locked or settled session"
        )

    # Verify participant is in session
    participant = await crud.get_participant(db, assignment_data.participant_id)
    if not participant or participant not in session.participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant not in session"
        )

    assignment = await crud.create_assignment(db, item, assignment_data)

    # Broadcast assignment
    await broadcast_to_session(
        session.id,
        {
            "type": "item_assigned",
            "data": {
                "assignment_id": assignment.id,
                "item_id": item.id,
                "participant_id": assignment.participant_id,
                "participant_name": participant.name,
                "share_percent": assignment.share_percent
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(
        db, session.id, "item_assigned",
        participant_id=participant.id,
        details=f"Item '{item.description}' assigned to {participant.name} ({assignment.share_percent}%)"
    )

    return assignment


# Assignment deletion router
assignment_router = APIRouter(prefix="/assignments", tags=["assignments"])


@assignment_router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
async def remove_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove an assignment"""
    assignment = await crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # Get item and session
    item = await db.get(Item, assignment.item_id)
    session = await crud.get_session_by_id(db, item.session_id)

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify assignments in locked or settled session"
        )

    participant_id = assignment.participant_id
    item_id = assignment.item_id

    await crud.delete_assignment(db, assignment)

    # Broadcast assignment removed
    await broadcast_to_session(
        session.id,
        {
            "type": "assignment_removed",
            "data": {
                "assignment_id": assignment_id,
                "item_id": item_id,
                "participant_id": participant_id
            }
        }
    )

    return {"success": True}
