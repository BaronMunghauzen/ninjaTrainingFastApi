from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.achievements.service import AchievementService
from app.achievements.schemas import (
    AchievementTypeCreate, AchievementTypeUpdate, AchievementTypeDisplay,
    AchievementCreate, AchievementUpdate, AchievementDisplay,
    UserAchievementsResponse, AchievementCheckResponse
)
from app.achievements.dao import AchievementTypeDAO, AchievementDAO
from app.users.dao import UsersDAO
from typing import List
import uuid

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.post("/types", response_model=AchievementTypeDisplay)
async def create_achievement_type(
    achievement_type: AchievementTypeCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать новый тип достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    return await achievement_type_dao.create_achievement_type(**achievement_type.dict())


@router.get("/types", response_model=List[AchievementTypeDisplay])
async def get_achievement_types(
    category: str = None,
    active_only: bool = True,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все типы достижений"""
    achievement_type_dao = AchievementTypeDAO(session)
    
    if category:
        return await achievement_type_dao.find_by_category(category)
    elif active_only:
        return await achievement_type_dao.find_active()
    else:
        return await achievement_type_dao.find_all()


@router.get("/types/{achievement_type_uuid}", response_model=AchievementTypeDisplay)
async def get_achievement_type(
    achievement_type_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить тип достижения по UUID"""
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_type = await achievement_type_dao.find_by_uuid(achievement_type_uuid)
    
    if not achievement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тип достижения не найден"
        )
    
    return achievement_type


@router.put("/types/{achievement_type_uuid}", response_model=AchievementTypeDisplay)
async def update_achievement_type(
    achievement_type_uuid: str,
    achievement_type_update: AchievementTypeUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Обновить тип достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_type = await achievement_type_dao.find_by_uuid(achievement_type_uuid)
    
    if not achievement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тип достижения не найден"
        )
    
    for field, value in achievement_type_update.dict(exclude_unset=True).items():
        setattr(achievement_type, field, value)
    
    await session.commit()
    await session.refresh(achievement_type)
    return achievement_type


@router.delete("/types/{achievement_type_uuid}")
async def delete_achievement_type(
    achievement_type_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить тип достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_type = await achievement_type_dao.find_by_uuid(achievement_type_uuid)
    
    if not achievement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тип достижения не найден"
        )
    
    await achievement_type_dao.delete(achievement_type)
    return {"message": "Тип достижения удален"}


# Роуты для проверки достижений
@router.post("/check-early-bird/{user_uuid}", response_model=AchievementCheckResponse)
async def check_early_bird_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'Ранняя пташка'"""
    service = AchievementService(session)
    return await service.check_early_bird_achievement(user_uuid)


@router.post("/check-night-owl/{user_uuid}", response_model=AchievementCheckResponse)
async def check_night_owl_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'Сова'"""
    service = AchievementService(session)
    return await service.check_night_owl_achievement(user_uuid)


@router.post("/check-new-year/{user_uuid}", response_model=AchievementCheckResponse)
async def check_new_year_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'С Новым годом'"""
    service = AchievementService(session)
    return await service.check_new_year_achievement(user_uuid)


@router.post("/check-womens-day/{user_uuid}", response_model=AchievementCheckResponse)
async def check_womens_day_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'Международный женский день'"""
    service = AchievementService(session)
    return await service.check_womens_day_achievement(user_uuid)


@router.post("/check-mens-day/{user_uuid}", response_model=AchievementCheckResponse)
async def check_mens_day_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'Мужской день'"""
    service = AchievementService(session)
    return await service.check_mens_day_achievement(user_uuid)


@router.post("/check-power-and-strength/{user_uuid}", response_model=AchievementCheckResponse)
async def check_power_and_strength_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение 'Мощь и сила'"""
    service = AchievementService(session)
    return await service.check_power_and_strength_achievement(user_uuid)


@router.post("/check-training-count/{user_uuid}", response_model=List[AchievementCheckResponse])
async def check_training_count_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить количественные достижения"""
    service = AchievementService(session)
    return await service.check_training_count_achievements(user_uuid)


@router.post("/check-weekly-training/{user_uuid}", response_model=List[AchievementCheckResponse])
async def check_weekly_training_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить недельные достижения"""
    service = AchievementService(session)
    return await service.check_weekly_training_achievements(user_uuid)


@router.post("/check-consecutive-weeks/{user_uuid}", response_model=List[AchievementCheckResponse])
async def check_consecutive_weeks_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижения за непрерывные недели"""
    service = AchievementService(session)
    return await service.check_consecutive_weeks_achievements(user_uuid)


@router.post("/check-consecutive-months/{user_uuid}", response_model=List[AchievementCheckResponse])
async def check_consecutive_months_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижения за непрерывные месяцы"""
    service = AchievementService(session)
    return await service.check_consecutive_months_achievements(user_uuid)


@router.post("/check-year-without-breaks/{user_uuid}", response_model=AchievementCheckResponse)
async def check_year_without_breaks_achievement(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить достижение '1 год без перерывов'"""
    service = AchievementService(session)
    return await service.check_year_without_breaks_achievement(user_uuid)


@router.post("/check-all/{user_uuid}", response_model=List[AchievementCheckResponse])
async def check_all_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Проверить все достижения для пользователя"""
    service = AchievementService(session)
    return await service.check_all_achievements_for_user(user_uuid)


# Роуты для работы с достижениями пользователей
@router.post("/", response_model=AchievementDisplay)
async def create_achievement(
    achievement: AchievementCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать новое достижение для пользователя"""
    achievement_dao = AchievementDAO(session)
    return await achievement_dao.create_achievement(**achievement.dict())


@router.get("/user/{user_uuid}", response_model=UserAchievementsResponse)
async def get_user_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все достижения пользователя"""
    users_dao = UsersDAO(session)
    achievement_dao = AchievementDAO(session)
    
    user = await users_dao.find_by_uuid(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    achievements = await achievement_dao.find_by_user_id(user.id)
    
    return UserAchievementsResponse(
        user_id=user.id,
        achievements=achievements,
        total_count=len(achievements)
    )


@router.get("/{achievement_uuid}", response_model=AchievementDisplay)
async def get_achievement(
    achievement_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить достижение по UUID"""
    achievement_dao = AchievementDAO(session)
    achievement = await achievement_dao.find_by_uuid(achievement_uuid)
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Достижение не найдено"
        )
    
    return achievement


@router.put("/{achievement_uuid}", response_model=AchievementDisplay)
async def update_achievement(
    achievement_uuid: str,
    achievement_update: AchievementUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Обновить достижение"""
    achievement_dao = AchievementDAO(session)
    achievement = await achievement_dao.find_by_uuid(achievement_uuid)
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Достижение не найдено"
        )
    
    for field, value in achievement_update.dict(exclude_unset=True).items():
        setattr(achievement, field, value)
    
    await session.commit()
    await session.refresh(achievement)
    return achievement


@router.delete("/{achievement_uuid}")
async def delete_achievement(
    achievement_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить достижение"""
    achievement_dao = AchievementDAO(session)
    achievement = await achievement_dao.find_by_uuid(achievement_uuid)
    
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Достижение не найдено"
        )
    
    await achievement_dao.delete(achievement)
    return {"message": "Достижение удалено"}
