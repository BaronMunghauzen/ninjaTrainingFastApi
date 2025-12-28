from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.achievements.schemas import (
    AchievementTypeCreate, AchievementTypeUpdate, AchievementTypeDisplay,
    AchievementCreate, AchievementUpdate, AchievementDisplay,
    UserAchievementsResponse, UserAchievementTypesResponse, AchievementTypeWithStatus
)
from app.achievements.dao import AchievementTypeDAO, AchievementDAO
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_admin_user
from app.files.service import FileService
from typing import List
from uuid import UUID
import uuid

router = APIRouter(prefix="/achievements", tags=["achievements"])


async def achievement_to_display(achievement, session: AsyncSession) -> AchievementDisplay:
    """Преобразует модель Achievement в AchievementDisplay с uuid вместо id"""
    from sqlalchemy import select
    from app.achievements.models import AchievementType
    
    # Получаем achievement_type
    try:
        achievement_type = achievement.achievement_type
    except AttributeError:
        achievement_type = None
    
    if not achievement_type and achievement.achievement_type_id:
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(AchievementType)
            .options(selectinload(AchievementType.image))
            .where(AchievementType.id == achievement.achievement_type_id)
        )
        achievement_type = result.scalar_one_or_none()
    
    # Получаем image_uuid для achievement_type
    image_uuid = None
    if achievement_type:
        try:
            image_uuid = achievement_type.image.uuid if achievement_type.image else None
        except AttributeError:
            # Если relationship не загружен
            if achievement_type.image_id:
                from app.files.models import File
                result = await session.execute(
                    select(File).where(File.id == achievement_type.image_id)
                )
                file_obj = result.scalar_one_or_none()
                image_uuid = file_obj.uuid if file_obj else None
    
    # Получаем uuid связанных объектов
    user_uuid = None
    if achievement.user_id:
        try:
            user_uuid = achievement.user.uuid
        except AttributeError:
            user = await UsersDAO.find_one_or_none_by_id(achievement.user_id)
            user_uuid = user.uuid if user else None
    
    user_training_uuid = None
    if achievement.user_training_id:
        try:
            user_training_uuid = achievement.user_training.uuid
        except AttributeError:
            from app.user_training.dao import UserTrainingDAO
            user_training = await UserTrainingDAO.find_one_or_none_by_id(achievement.user_training_id)
            user_training_uuid = user_training.uuid if user_training else None
    
    user_program_uuid = None
    if achievement.user_program_id:
        try:
            user_program_uuid = achievement.user_program.uuid
        except AttributeError:
            from app.user_program.dao import UserProgramDAO
            user_program = await UserProgramDAO.find_one_or_none_by_id(achievement.user_program_id)
            user_program_uuid = user_program.uuid if user_program else None
    
    program_uuid = None
    if achievement.program_id:
        try:
            program_uuid = achievement.program.uuid
        except AttributeError:
            from app.programs.dao import ProgramDAO
            program = await ProgramDAO.find_one_or_none_by_id(achievement.program_id)
            program_uuid = program.uuid if program else None
    
    return AchievementDisplay(
        uuid=achievement.uuid,
        achievement_type=AchievementTypeDisplay(
            uuid=achievement_type.uuid,
            name=achievement_type.name,
            description=achievement_type.description,
            category=achievement_type.category,
            subcategory=achievement_type.subcategory,
            requirements=achievement_type.requirements,
            icon=achievement_type.icon,
            points=achievement_type.points,
            is_active=achievement_type.is_active,
            image_uuid=image_uuid,
            created_at=achievement_type.created_at,
            updated_at=achievement_type.updated_at
        ) if achievement_type else None,
        user_uuid=user_uuid,
        status=achievement.status,
        user_training_uuid=user_training_uuid,
        user_program_uuid=user_program_uuid,
        program_uuid=program_uuid,
        training_date=achievement.training_date,
        completed_at=achievement.completed_at,
        created_at=achievement.created_at,
        updated_at=achievement.updated_at,
        name=achievement.display_name
    )


@router.post("/types", response_model=AchievementTypeDisplay)
async def create_achievement_type(
    achievement_type: AchievementTypeCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать новый тип достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    created = await achievement_type_dao.create_achievement_type(**achievement_type.dict())
    # Преобразуем image_id в image_uuid
    image_uuid = created.image.uuid if created.image else None
    return AchievementTypeDisplay(
        uuid=created.uuid,
        name=created.name,
        description=created.description,
        category=created.category,
        subcategory=created.subcategory,
        requirements=created.requirements,
        icon=created.icon,
        points=created.points,
        is_active=created.is_active,
        image_uuid=image_uuid,
        created_at=created.created_at,
        updated_at=created.updated_at
    )


@router.get("/types", response_model=List[AchievementTypeDisplay])
async def get_achievement_types(
    category: str = None,
    active_only: bool = True,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все типы достижений"""
    achievement_type_dao = AchievementTypeDAO(session)
    
    if category:
        achievement_types = await achievement_type_dao.find_by_category(category)
    elif active_only:
        achievement_types = await achievement_type_dao.find_active()
    else:
        achievement_types = await achievement_type_dao.find_all()
    
    # Преобразуем в схемы с image_uuid
    return [
        AchievementTypeDisplay(
            uuid=at.uuid,
            name=at.name,
            description=at.description,
            category=at.category,
            subcategory=at.subcategory,
            requirements=at.requirements,
            icon=at.icon,
            points=at.points,
            is_active=at.is_active,
            image_uuid=at.image.uuid if at.image else None,
            created_at=at.created_at,
            updated_at=at.updated_at
        )
        for at in achievement_types
    ]


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
    
    image_uuid = achievement_type.image.uuid if achievement_type.image else None
    return AchievementTypeDisplay(
        uuid=achievement_type.uuid,
        name=achievement_type.name,
        description=achievement_type.description,
        category=achievement_type.category,
        subcategory=achievement_type.subcategory,
        requirements=achievement_type.requirements,
        icon=achievement_type.icon,
        points=achievement_type.points,
        is_active=achievement_type.is_active,
        image_uuid=image_uuid,
        created_at=achievement_type.created_at,
        updated_at=achievement_type.updated_at
    )


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
    
    image_uuid = achievement_type.image.uuid if achievement_type.image else None
    return AchievementTypeDisplay(
        uuid=achievement_type.uuid,
        name=achievement_type.name,
        description=achievement_type.description,
        category=achievement_type.category,
        subcategory=achievement_type.subcategory,
        requirements=achievement_type.requirements,
        icon=achievement_type.icon,
        points=achievement_type.points,
        is_active=achievement_type.is_active,
        image_uuid=image_uuid,
        created_at=achievement_type.created_at,
        updated_at=achievement_type.updated_at
    )


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


@router.post("/types/{achievement_type_uuid}/upload-image", summary="Загрузить изображение для типа достижения")
async def upload_achievement_type_image(
    achievement_type_uuid: str,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Загрузить изображение для типа достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_type = await achievement_type_dao.find_by_uuid(achievement_type_uuid)
    
    if not achievement_type:
        raise HTTPException(status_code=404, detail="Тип достижения не найден")
    
    old_file_uuid = getattr(achievement_type.image, 'uuid', None) if achievement_type.image else None
    
    saved_file = await FileService.save_file(
        file=file,
        entity_type="achievement_type",
        entity_id=achievement_type.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    
    await AchievementTypeDAO.update(UUID(achievement_type_uuid), image_id=saved_file.id)
    
    return {"message": "Изображение успешно загружено", "image_uuid": str(saved_file.uuid)}


@router.delete("/types/{achievement_type_uuid}/delete-image", summary="Удалить изображение типа достижения")
async def delete_achievement_type_image(
    achievement_type_uuid: str,
    user_data = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Удалить изображение типа достижения"""
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_type = await achievement_type_dao.find_by_uuid(achievement_type_uuid)
    
    if not achievement_type:
        raise HTTPException(status_code=404, detail="Тип достижения не найден")
    
    if not achievement_type.image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    image_uuid = achievement_type.image.uuid
    
    # Сначала обновляем image_id в achievement_types (устанавливаем в None)
    # Это нужно сделать до удаления файла, чтобы избежать нарушения внешнего ключа
    achievement_type.image_id = None
    await session.commit()
    await session.refresh(achievement_type)
    
    # Теперь удаляем файл
    try:
        await FileService.delete_file_by_uuid(str(image_uuid))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении файла: {str(e)}"
        )
    
    return {"message": "Изображение успешно удалено"}


# Роуты для работы с достижениями пользователей
@router.post("/", response_model=AchievementDisplay)
async def create_achievement(
    achievement: AchievementCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Создать новое достижение для пользователя"""
    achievement_dao = AchievementDAO(session)
    created_achievement = await achievement_dao.create_achievement(**achievement.dict())
    return await achievement_to_display(created_achievement, session)


@router.get("/user/{user_uuid}", response_model=UserAchievementTypesResponse)
async def get_user_achievements(
    user_uuid: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Получить все типы достижений с информацией о том, какие из них получены пользователем"""
    from sqlalchemy import select, and_
    from app.achievements.models import Achievement
    
    achievement_type_dao = AchievementTypeDAO(session)
    achievement_dao = AchievementDAO(session)
    
    user = await UsersDAO.find_by_uuid(user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Получаем все типы достижений
    achievement_types = await achievement_type_dao.find_all()
    
    # Получаем все достижения пользователя для быстрой проверки
    user_achievements = await achievement_dao.find_by_user_id(user.id)
    user_achievement_type_ids = {achievement.achievement_type_id for achievement in user_achievements if achievement.achievement_type_id}
    
    # Формируем ответ с статусом для каждого типа
    achievement_types_with_status = []
    for achievement_type in achievement_types:
        status = "earned" if achievement_type.id in user_achievement_type_ids else "not_earned"
        
        # Получаем image_uuid если есть image
        image_uuid = None
        try:
            image_uuid = achievement_type.image.uuid if achievement_type.image else None
        except AttributeError:
            # Если relationship не загружен, делаем запрос
            if achievement_type.image_id:
                from sqlalchemy import select
                from app.files.models import File
                result = await session.execute(
                    select(File).where(File.id == achievement_type.image_id)
                )
                file_obj = result.scalar_one_or_none()
                image_uuid = file_obj.uuid if file_obj else None
        
        achievement_type_with_status = AchievementTypeWithStatus(
            uuid=achievement_type.uuid,
            name=achievement_type.name,
            description=achievement_type.description,
            category=achievement_type.category,
            subcategory=achievement_type.subcategory,
            requirements=achievement_type.requirements,
            icon=achievement_type.icon,
            points=achievement_type.points,
            is_active=achievement_type.is_active,
            image_uuid=image_uuid,
            status=status,
            created_at=achievement_type.created_at,
            updated_at=achievement_type.updated_at
        )
        achievement_types_with_status.append(achievement_type_with_status)
    
    return UserAchievementTypesResponse(
        achievement_types=achievement_types_with_status,
        total_count=len(achievement_types_with_status)
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
    
    return await achievement_to_display(achievement, session)


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
    return await achievement_to_display(achievement, session)


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
