from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.business.schemas import (
    BusinessCreateRequest,
    BusinessResponse,
    BusinessSettingsResponse,
    BusinessSettingsUpdateRequest,
    BusinessUpdateRequest,
)
from app.api.business.service import BusinessService
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User

router = APIRouter()


@router.get("", response_model=List[BusinessResponse])
async def list_businesses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's businesses (SRS Module 3)."""
    return await BusinessService.list_businesses(db, current_user)


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    payload: BusinessCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a business (status 'draft' = Save Draft, 'active' = Create Business)."""
    return await BusinessService.create_business(db, current_user, payload)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await BusinessService.get_business(db, current_user, business_id)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: int,
    payload: BusinessUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a business / activate a draft (SRS Module 3: Edit, Create Business)."""
    return await BusinessService.update_business(db, current_user, business_id, payload)


@router.get("/{business_id}/settings", response_model=BusinessSettingsResponse)
async def get_business_settings(
    business_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SRS Module 4 — read the Business Configuration toggles."""
    return await BusinessService.get_settings(db, current_user, business_id)


@router.patch("/{business_id}/settings", response_model=BusinessSettingsResponse)
async def update_business_settings(
    business_id: int,
    payload: BusinessSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SRS Module 4 — Business Configuration Wizard. Manufacturing requires Inventory."""
    return await BusinessService.update_settings(db, current_user, business_id, payload)
