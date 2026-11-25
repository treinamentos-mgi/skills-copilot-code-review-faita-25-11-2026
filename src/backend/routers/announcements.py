"""Announcement endpoints for the High School Management System API."""

from datetime import date
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import announcements_collection
from .auth import get_current_teacher

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    expires_at: date
    starts_at: Optional[date] = None


def serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(announcement["_id"]),
        "message": announcement["message"],
        "starts_at": announcement.get("starts_at"),
        "expires_at": announcement["expires_at"]
    }


def announcement_values(payload: AnnouncementPayload) -> Dict[str, Any]:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank")
    if payload.starts_at and payload.starts_at > payload.expires_at:
        raise HTTPException(
            status_code=422,
            detail="Start date must be on or before the expiration date"
        )
    values = {
        "message": message,
        "starts_at": payload.starts_at.isoformat() if payload.starts_at else None,
        "expires_at": payload.expires_at.isoformat()
    }
    return values


def get_announcement_id(announcement_id: str) -> ObjectId:
    if not ObjectId.is_valid(announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ObjectId(announcement_id)


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements currently within their optional start and expiry dates."""
    today = date.today().isoformat()
    query = {
        "expires_at": {"$gte": today},
        "$or": [
            {"starts_at": {"$exists": False}},
            {"starts_at": None},
            {"starts_at": {"$lte": today}}
        ]
    }
    return [
        serialize_announcement(item)
        for item in announcements_collection.find(query).sort("expires_at", 1)
    ]


@router.get("/manage", response_model=List[Dict[str, Any]])
def list_announcements(
    _: Dict[str, Any] = Depends(get_current_teacher)
) -> List[Dict[str, Any]]:
    """List all announcements for an authenticated teacher."""
    return [
        serialize_announcement(item)
        for item in announcements_collection.find().sort("expires_at", -1)
    ]


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_announcement(
    payload: AnnouncementPayload,
    _: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Create an announcement. Expiration date is required."""
    announcement = announcement_values(payload)
    result = announcements_collection.insert_one(announcement)
    return serialize_announcement({"_id": result.inserted_id, **announcement})


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    _: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Update an announcement. Expiration date is required."""
    object_id = get_announcement_id(announcement_id)
    announcement = announcement_values(payload)
    result = announcements_collection.find_one_and_update(
        {"_id": object_id}, {"$set": announcement}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return serialize_announcement({"_id": object_id, **announcement})


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    _: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, str]:
    """Delete an announcement."""
    object_id = get_announcement_id(announcement_id)
    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted"}