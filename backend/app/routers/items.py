# backend/app/routers/items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models import Item, Session, SessionStatus
from app.schemas import (
    ItemCreate, ItemResponse, ItemWithAssignments,
    ItemUpdate, DisputeRequest
)
from app import crud
from app.websocket import broadcast_to_session

router = APIRouter(prefix="/sessions/{session_id}/items", tags=["items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    session_id: int,
    item_data: ItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a manual item to session"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add items to locked or settled session"
        )

    item = await crud.create_item(db, session, item_data)

    # Broadcast item added
    await broadcast_to_session(
        session.id,
        {
            "type": "item_added",
            "data": {
                "id": item.id,
                "description": item.description,
                "amount": item.amount,
                "quantity": item.quantity
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(
        db, session.id, "item_added",
        details=f"Item '{item.description}' (${item.amount}) added"
    )

    return item


@router.post("/bulk", response_model=List[ItemResponse], status_code=status.HTTP_201_CREATED)
async def create_items_bulk(
    session_id: int,
    items_data: List[ItemCreate],
    db: AsyncSession = Depends(get_db)
):
    """Add multiple items at once (from OCR)"""
    session = await crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add items to locked or settled session"
        )

    items = await crud.create_items_bulk(db, session, items_data)

    # Broadcast all items added
    await broadcast_to_session(
        session.id,
        {
            "type": "item_added",
            "data": {
                "items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "amount": item.amount,
                        "quantity": item.quantity
                    }
                    for item in items
                ],
                "bulk": True
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(
        db, session.id, "items_added_bulk",
        details=f"{len(items)} items added via OCR"
    )

    return items


# Individual item operations
item_router = APIRouter(prefix="/items", tags=["items"])


@item_router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    update_data: ItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update item details"""
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
            detail="Cannot modify items in locked or settled session"
        )

    item = await crud.update_item(
        db, item,
        description=update_data.description,
        amount=update_data.amount,
        quantity=update_data.quantity
    )

    # Broadcast item updated
    await broadcast_to_session(
        session.id,
        {
            "type": "item_updated",
            "data": {
                "id": item.id,
                "description": item.description,
                "amount": item.amount,
                "quantity": item.quantity
            }
        }
    )

    return item


@item_router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove an item"""
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
            detail="Cannot delete items from locked or settled session"
        )

    session_id = session.id
    item_description = item.description

    await crud.delete_item(db, item)

    # Broadcast item removed
    await broadcast_to_session(
        session_id,
        {
            "type": "item_removed",
            "data": {"item_id": item_id}
        }
    )

    return {"success": True}


@item_router.post("/{item_id}/dispute", response_model=ItemResponse)
async def dispute_item(
    item_id: int,
    dispute_data: DisputeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Flag an item as disputed"""
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
            detail="Cannot dispute items in locked or settled session"
        )

    item = await crud.dispute_item(db, item, dispute_data.reason)

    # Broadcast item disputed
    await broadcast_to_session(
        session.id,
        {
            "type": "item_disputed",
            "data": {
                "item_id": item.id,
                "reason": item.dispute_reason
            }
        }
    )

    # Create audit log
    await crud.create_audit_log(
        db, session.id, "item_disputed",
        details=f"Item '{item.description}' disputed: {dispute_data.reason}"
    )

    return item
