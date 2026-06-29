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


class OtpSendRequest(BaseModel):
    """Ask the backend to have MSG91 send an OTP to this phone."""

    phone: str = Field(..., description="Indian mobile (E.164 +91… or 10 digits)")


class OtpVerifyRequest(BaseModel):
    """
    Verify the OTP the user typed, or the MSG91 SendOTP Widget access token.
    On success, the backend registers (first time, `fullName` required) or
    logs the user in.
    """

    phone: Optional[str] = Field(default=None, description="Same phone the OTP was sent to")
    otp: Optional[str] = Field(default=None, min_length=4, max_length=8, description="Code from SMS")
    accessToken: Optional[str] = Field(default=None, description="JWT access token from MSG91 SendOTP Widget")
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
