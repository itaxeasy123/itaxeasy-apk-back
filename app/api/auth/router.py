from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.schemas import (
    FirebaseAuthRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.api.auth.service import AuthService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/firebase", response_model=TokenResponse)
async def firebase_auth(
    payload: FirebaseAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register or log in with a verified Firebase phone OTP.

    The app runs the Firebase Phone Auth flow (Send OTP / Verify OTP) on-device,
    then posts the resulting Firebase ID token here. We verify it, create the
    account on first contact (registration) or load the existing one (login),
    and return our own access + refresh tokens.
    """
    user, access_token, refresh_token, is_new = await AuthService.authenticate_with_firebase(
        db,
        id_token=payload.idToken,
        full_name=payload.fullName,
        email=payload.email,
        device_info=payload.deviceInfo,
        ip_address=_client_ip(request),
    )
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        isNewUser=is_new,
        user=user,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Rotate a refresh token for a fresh access + refresh token pair."""
    user, access_token, refresh_token = await AuthService.refresh_tokens(
        db,
        raw_refresh=payload.refreshToken,
        device_info=None,
        ip_address=_client_ip(request),
    )
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=user,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Revoke a refresh-token session (SRS Module 2: Logout)."""
    await AuthService.logout(db, payload.refreshToken)
    return {"success": True, "message": "Logged out."}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile (SRS Module 2)."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit the authenticated user's profile (SRS Module 2: Edit Profile)."""
    return await AuthService.update_profile(db, current_user, payload)
