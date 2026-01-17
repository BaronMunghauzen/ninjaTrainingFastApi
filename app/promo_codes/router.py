"""
API роутер для работы с промокодами
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.users.dependencies import get_current_admin_user
from app.users.models import User
from app.promo_codes.dao import PromoCodeDAO
from app.promo_codes.schemas import (
    SPromoCodeResponse,
    SPromoCodeAdd,
    SPromoCodeUpdate
)

router = APIRouter(prefix='/api/promo_codes', tags=['Promo Codes'])


@router.get("/", response_model=List[SPromoCodeResponse])
async def get_all_promo_codes(admin: User = Depends(get_current_admin_user)):
    """
    Получить список всех промокодов (только для админов)
    """
    try:
        promo_codes = await PromoCodeDAO.find_all()
        return promo_codes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения промокодов: {str(e)}"
        )


@router.get("/{promo_code_uuid}", response_model=SPromoCodeResponse)
async def get_promo_code_by_uuid(
    promo_code_uuid: UUID,
    admin: User = Depends(get_current_admin_user)
):
    """
    Получить промокод по UUID (только для админов)
    """
    try:
        promo_code = await PromoCodeDAO.find_full_data(promo_code_uuid)
        if not promo_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Промокод не найден"
            )
        return promo_code
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения промокода: {str(e)}"
        )


@router.post("/", response_model=SPromoCodeResponse)
async def create_promo_code(
    promo_code_data: SPromoCodeAdd,
    admin: User = Depends(get_current_admin_user)
):
    """
    Создать новый промокод (только для админов)
    """
    try:
        # Проверяем, не существует ли уже промокод с таким кодом
        existing = await PromoCodeDAO.find_by_code(promo_code_data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Промокод с кодом '{promo_code_data.code}' уже существует"
            )
        
        # Создаем промокод (нормализуем код в верхний регистр)
        promo_code_dict = promo_code_data.model_dump()
        promo_code_dict['code'] = promo_code_dict['code'].upper().strip()
        promo_code_uuid = await PromoCodeDAO.add(**promo_code_dict)
        
        # Получаем созданный промокод
        promo_code = await PromoCodeDAO.find_full_data(promo_code_uuid)
        return promo_code
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания промокода: {str(e)}"
        )


@router.put("/{promo_code_uuid}", response_model=SPromoCodeResponse)
async def update_promo_code(
    promo_code_uuid: UUID,
    promo_code_data: SPromoCodeUpdate,
    admin: User = Depends(get_current_admin_user)
):
    """
    Обновить промокод (только для админов)
    """
    try:
        # Проверяем существование промокода
        existing = await PromoCodeDAO.find_full_data(promo_code_uuid)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Промокод не найден"
            )
        
        # Если изменяется код, проверяем уникальность (нормализуем код в верхний регистр)
        if promo_code_data.code:
            normalized_code = promo_code_data.code.upper().strip()
            if normalized_code != existing.code:
                code_exists = await PromoCodeDAO.find_by_code(normalized_code)
            if code_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Промокод с кодом '{promo_code_data.code}' уже существует"
                )
        
        # Обновляем промокод (нормализуем код в верхний регистр, если он изменяется)
        update_data = promo_code_data.model_dump(exclude_unset=True)
        if 'code' in update_data:
            update_data['code'] = update_data['code'].upper().strip()
        if update_data:
            await PromoCodeDAO.update(promo_code_uuid, **update_data)
        
        # Получаем обновленный промокод
        updated_promo_code = await PromoCodeDAO.find_full_data(promo_code_uuid)
        return updated_promo_code
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обновления промокода: {str(e)}"
        )


@router.delete("/{promo_code_uuid}")
async def delete_promo_code(
    promo_code_uuid: UUID,
    admin: User = Depends(get_current_admin_user)
):
    """
    Удалить промокод (только для админов)
    """
    try:
        # Проверяем существование промокода
        existing = await PromoCodeDAO.find_full_data(promo_code_uuid)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Промокод не найден"
            )
        
        # Удаляем промокод
        await PromoCodeDAO.delete_by_id(promo_code_uuid)
        
        return {"message": "Промокод успешно удален"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления промокода: {str(e)}"
        )

