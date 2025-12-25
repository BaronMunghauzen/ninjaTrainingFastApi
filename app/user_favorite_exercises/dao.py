from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.dao.base import BaseDAO
from app.user_favorite_exercises.models import UserFavoriteExercise
from app.database import async_session_maker
from app.users.dao import UsersDAO
from app.exercise_reference.dao import ExerciseReferenceDAO
from fastapi import HTTPException, status


class UserFavoriteExerciseDAO(BaseDAO):
    model = UserFavoriteExercise
    uuid_fk_map = {
        'user_id': (UsersDAO, 'user_uuid'),
        'exercise_reference_id': (ExerciseReferenceDAO, 'exercise_reference_uuid'),
    }

    @classmethod
    async def is_favorite(cls, user_id: int, exercise_reference_id: int) -> bool:
        """Проверяет, является ли упражнение избранным для пользователя"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(
                user_id=user_id,
                exercise_reference_id=exercise_reference_id
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @classmethod
    async def add_to_favorites(cls, user_id: int, exercise_reference_id: int) -> UUID:
        """Добавляет упражнение в избранное пользователя"""
        async with async_session_maker() as session:
            async with session.begin():
                # Проверяем, не добавлено ли уже в той же сессии
                query = select(cls.model).filter_by(
                    user_id=user_id,
                    exercise_reference_id=exercise_reference_id
                )
                result = await session.execute(query)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Уже в избранном, возвращаем UUID существующей записи
                    return existing.uuid
                
                # Создаем новую запись
                new_favorite = cls.model(
                    user_id=user_id,
                    exercise_reference_id=exercise_reference_id
                )
                session.add(new_favorite)
                await session.flush()
                await session.refresh(new_favorite)
                return new_favorite.uuid

    @classmethod
    async def remove_from_favorites(cls, user_id: int, exercise_reference_id: int) -> bool:
        """Удаляет упражнение из избранного пользователя"""
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(
                    user_id=user_id,
                    exercise_reference_id=exercise_reference_id
                )
                result = await session.execute(query)
                favorite = result.scalar_one_or_none()
                
                if not favorite:
                    return False
                
                await session.delete(favorite)
                await session.flush()
                return True

    @classmethod
    async def get_user_favorites(cls, user_id: int):
        """Получает все избранные упражнения пользователя"""
        async with async_session_maker() as session:
            query = select(cls.model).options(
                joinedload(cls.model.exercise_reference).joinedload("image"),
                joinedload(cls.model.exercise_reference).joinedload("video"),
                joinedload(cls.model.exercise_reference).joinedload("gif"),
                joinedload(cls.model.exercise_reference).joinedload("user")
            ).filter_by(user_id=user_id)
            
            result = await session.execute(query)
            favorites = result.unique().scalars().all()
            
            # Отключаем объекты от сессии
            for fav in favorites:
                session.expunge(fav)
            
            return [fav.exercise_reference for fav in favorites if fav.exercise_reference]

    @classmethod
    async def get_user_favorite_exercise_ids(cls, user_id: int) -> set[int]:
        """Получает множество ID избранных упражнений пользователя (для оптимизации)"""
        async with async_session_maker() as session:
            query = select(cls.model.exercise_reference_id).filter_by(user_id=user_id)
            result = await session.execute(query)
            return set(result.scalars().all())

