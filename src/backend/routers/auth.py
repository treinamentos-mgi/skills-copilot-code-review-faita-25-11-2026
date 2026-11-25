"""
Authentication endpoints for the High School Management System API
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import sessions_collection, teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_teacher(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    """Resolve an unexpired login session to its teacher account."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    session = sessions_collection.find_one({
        "_id": credentials.credentials,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    teacher = teachers_collection.find_one({"_id": session["username"]})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher session")
    return teacher


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    sessions_collection.insert_one({
        "_id": session_token,
        "username": username,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=12)
    })

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": session_token
    }


@router.get("/check-session")
def check_session(
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Return the teacher associated with the authenticated session."""
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    teacher: Dict[str, Any] = Depends(get_current_teacher)
) -> Dict[str, str]:
    """Revoke the current login session."""
    sessions_collection.delete_one({"_id": credentials.credentials})
    return {"message": "Logged out"}
