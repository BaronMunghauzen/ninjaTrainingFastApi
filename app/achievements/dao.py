from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base import BaseDAO
from app.achievements.models import Achievement, AchievementType
from app.users.models import User
from app.user_training.models import UserTraining
from app.user_program.models import UserProgram
from app.programs.models import Program
import uuid
from datetime import datetime


class AchievementTypeDAO(BaseDAO):
    model = AchievementType

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_name(self, name: str) -> Optional[AchievementType]:
        """Найти тип достижения по имени"""
        result = await self.session.execute(
            select(AchievementType).where(AchievementType.name == name)
        )
        return result.scalar_one_or_none()

    async def find_by_category(self, category: str) -> List[AchievementType]:
        """Найти все типы достижений по категории"""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AchievementType)
            .options(selectinload(AchievementType.image))
            .where(AchievementType.category == category)
            .order_by(AchievementType.points)
        )
        return result.scalars().all()

    async def find_active(self) -> List[AchievementType]:
        """Найти все активные типы достижений"""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AchievementType)
            .options(selectinload(AchievementType.image))
            .where(AchievementType.is_active.is_(True))
            .order_by(AchievementType.points.nulls_last())
        )
        return result.scalars().all()

    async def find_all(self) -> List[AchievementType]:
        """Найти все типы достижений"""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AchievementType)
            .options(selectinload(AchievementType.image))
            .order_by(AchievementType.points.nulls_last())
        )
        return result.scalars().all()
    
    async def find_by_uuid(self, uuid: str) -> Optional[AchievementType]:
        """Найти тип достижения по UUID"""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(AchievementType)
            .options(selectinload(AchievementType.image))
            .where(AchievementType.uuid == uuid)
        )
        return result.scalar_one_or_none()

    async def create_achievement_type(
        self,
        name: str,
        description: str,
        category: str,
        subcategory: Optional[str] = None,
        requirements: Optional[str] = None,
        icon: Optional[str] = None,
        points: Optional[int] = None,
        is_active: bool = True,
        image_id: Optional[int] = None
    ) -> AchievementType:
        """Создать новый тип достижения"""
        achievement_type = AchievementType(
            uuid=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            subcategory=subcategory,
            requirements=requirements,
            icon=icon,
            points=points,
            is_active=is_active,
            image_id=image_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return await self.add(achievement_type)

    async def add(self, achievement_type: AchievementType) -> AchievementType:
        """Добавить тип достижения в базу"""
        self.session.add(achievement_type)
        await self.session.commit()
        await self.session.refresh(achievement_type)
        return achievement_type


class AchievementDAO(BaseDAO):
    model = Achievement

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_user_and_type(self, user_id: int, achievement_type_id: int) -> Optional[Achievement]:
        """Найти достижение пользователя по типу"""
        result = await self.session.execute(
            select(Achievement).where(
                and_(
                    Achievement.user_id == user_id,
                    Achievement.achievement_type_id == achievement_type_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int) -> List[Achievement]:
        """Найти все достижения пользователя"""
        result = await self.session.execute(
            select(Achievement)
            .where(Achievement.user_id == user_id)
            .order_by(Achievement.created_at.desc())
        )
        return result.scalars().all()

    async def find_by_name_and_user(self, name: str, user_id: int) -> Optional[Achievement]:
        """Найти достижение пользователя по имени типа достижения"""
        result = await self.session.execute(
            select(Achievement)
            .join(AchievementType)
            .where(
                and_(
                    AchievementType.name == name,
                    Achievement.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_achievement(
        self,
        achievement_type_id: int,
        user_id: int,
        user_training_id: Optional[int] = None,
        user_program_id: Optional[int] = None,
        program_id: Optional[int] = None,
        name: Optional[str] = None
    ) -> Achievement:
        """Создать новое достижение для пользователя"""
        # Если name не передан, получаем его из типа достижения
        if name is None:
            from app.achievements.models import AchievementType
            result = await self.session.execute(
                select(AchievementType).where(AchievementType.id == achievement_type_id)
            )
            achievement_type = result.scalar_one_or_none()
            name = achievement_type.name if achievement_type else ""
        
        achievement = Achievement(
            uuid=str(uuid.uuid4()),
            name=name,  # Заполняем поле name
            achievement_type_id=achievement_type_id,
            user_id=user_id,
            status="active",
            user_training_id=user_training_id,
            user_program_id=user_program_id,
            program_id=program_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return await self.add(achievement)

    async def add(self, achievement: Achievement) -> Achievement:
        """Добавить достижение в базу"""
        self.session.add(achievement)
        await self.session.commit()
        await self.session.refresh(achievement)
        return achievement

    async def check_achievement_exists(
        self,
        user_id: int,
        achievement_type_id: int
    ) -> bool:
        """Проверить, есть ли у пользователя достижение данного типа"""
        result = await self.session.execute(
            select(Achievement).where(
                and_(
                    Achievement.user_id == user_id,
                    Achievement.achievement_type_id == achievement_type_id
                )
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def find_by_uuid(self, uuid: str) -> Optional[Achievement]:
        """Найти достижение по UUID"""
        result = await self.session.execute(
            select(Achievement).where(Achievement.uuid == uuid)
        )
        return result.scalar_one_or_none()
