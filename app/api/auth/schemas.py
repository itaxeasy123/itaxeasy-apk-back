from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import UserGender, UserType


class UserResponse(BaseModel):
    id: int
    createdAt: datetime
    updatedAt: datetime
    phone: str
    email: Optional[EmailStr] = None
    fullName: str
    profilePhoto: Optional[str] = None
    timeZone: str
    language: str
    gender: Optional[UserGender] = None
    verified: bool
    userType: UserType

    class Config:
        from_attributes = True


class FirebaseAuthRequest(BaseModel):
    """
    Sent by the app after the Firebase Phone Auth SDK has verified the OTP.

    `idToken` is the Firebase ID token (the backend verifies it). `fullName`/
    `email` are only used the FIRST time (registration); on subsequent logins
    they are ignored and the stored profile is returned.
    """

    idToken: str = Field(..., description="Firebase ID token from the device SDK")
    fullName: Optional[str] = Field(
        default=None, min_length=3, description="Required on first-time registration"
    )
    email: Optional[EmailStr] = None
    deviceInfo: Optional[str] = Field(default=None, description="Optional device label")


class RefreshRequest(BaseModel):
    refreshToken: str


class ProfileUpdateRequest(BaseModel):
    fullName: Optional[str] = Field(default=None, min_length=3)
    email: Optional[EmailStr] = None
    profilePhoto: Optional[str] = None
    timeZone: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[UserGender] = None


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    isNewUser: bool = False
    user: UserResponse
