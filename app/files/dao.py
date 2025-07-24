from app.dao.base import BaseDAO
from app.files.models import File
from sqlalchemy import select, delete, desc, update
from app.programs.models import Program
from app.trainings.models import Training
from app.exercise_groups.models import ExerciseGroup
from app.exercises.models import Exercise


class FilesDAO(BaseDAO):
    model = File
    
    @classmethod
    async def find_by_entity(cls, entity_type: str, entity_id: int):
        """Поиск файлов по типу и ID сущности"""
        return await cls.find_all(entity_type=entity_type, entity_id=entity_id)
    
    @classmethod
    async def find_avatar_by_user_id(cls, user_id: int):
        """Поиск аватара пользователя (возвращает самый новый файл)"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .where(cls.model.entity_type == "user", cls.model.entity_id == user_id)
                .order_by(desc(cls.model.created_at))
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def find_by_uuid(cls, file_uuid: str):
        """Поиск файла по UUID с правильной обработкой типов"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            query = select(cls.model).where(cls.model.uuid == file_uuid)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @classmethod
    async def delete_by_uuid(cls, file_uuid: str):
        """Удаление файла по UUID (строка)"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            async with session.begin():
                # Сначала проверяем, что файл существует
                query = select(cls.model).where(cls.model.uuid == file_uuid)
                result = await session.execute(query)
                file_to_delete = result.scalar_one_or_none()

                if not file_to_delete:
                    raise Exception(f"Файл с UUID {file_uuid} не найден")

                # Удаляем файл
                await session.execute(
                    delete(cls.model).where(cls.model.uuid == file_uuid)
                )
                await session.commit()
                return file_uuid
    
    @classmethod
    async def delete_file_with_cleanup(cls, file_uuid: str):
        """Удаление файла с очисткой ссылок в одной транзакции"""
        from app.database import async_session_maker
        from app.users.models import User
        from sqlalchemy import update
        
        async with async_session_maker() as session:
            async with session.begin():
                # Сначала проверяем, что файл существует
                query = select(cls.model).where(cls.model.uuid == file_uuid)
                result = await session.execute(query)
                file_to_delete = result.scalar_one_or_none()

                if not file_to_delete:
                    raise Exception(f"Файл с UUID {file_uuid} не найден")

                file_id = getattr(file_to_delete, 'id', None)
                if file_id is not None:
                    # Очищаем ссылки на файл в таблице пользователей
                    update_query = (
                        update(User)
                        .where(User.avatar_id == file_id)
                        .values(avatar_id=None)
                    )
                    await session.execute(update_query)

                    # Очищаем ссылки на файл в таблице программ
                    await session.execute(
                        update(Program)
                        .where(Program.image_id == file_id)
                        .values(image_id=None)
                    )
                    # Очищаем ссылки на файл в таблице тренировок
                    await session.execute(
                        update(Training)
                        .where(Training.image_id == file_id)
                        .values(image_id=None)
                    )
                    # Очищаем ссылки на файл в таблице групп упражнений
                    await session.execute(
                        update(ExerciseGroup)
                        .where(ExerciseGroup.image_id == file_id)
                        .values(image_id=None)
                    )
                    # Очищаем ссылки на файл в таблице упражнений (image_id, video_id, video_preview_id)
                    await session.execute(
                        update(Exercise)
                        .where(Exercise.image_id == file_id)
                        .values(image_id=None)
                    )
                    await session.execute(
                        update(Exercise)
                        .where(Exercise.video_id == file_id)
                        .values(video_id=None)
                    )
                    await session.execute(
                        update(Exercise)
                        .where(Exercise.video_preview_id == file_id)
                        .values(video_preview_id=None)
                    )

                # Удаляем файл
                await session.execute(
                    delete(cls.model).where(cls.model.uuid == file_uuid)
                )
                
                await session.commit()
                return file_uuid
    
    @classmethod
    async def delete_old_avatars_for_user(cls, user_id: int, keep_latest: bool = True):
        """Удаление старых аватаров пользователя, оставляя только самый новый"""
        from app.database import async_session_maker
        async with async_session_maker() as session:
            async with session.begin():
                # Получаем все файлы аватаров пользователя, отсортированные по дате создания
                query = (
                    select(cls.model)
                    .where(cls.model.entity_type == "user", cls.model.entity_id == user_id)
                    .order_by(desc(cls.model.created_at))
                )
                result = await session.execute(query)
                avatars = result.scalars().all()
                
                if len(avatars) <= 1:
                    return []  # Нет старых файлов для удаления
                
                # Если нужно оставить только самый новый
                if keep_latest:
                    avatars_to_delete = avatars[1:]  # Все кроме первого (самого нового)
                else:
                    avatars_to_delete = avatars
                
                # Удаляем старые файлы
                deleted_uuids = []
                for avatar in avatars_to_delete:
                    await session.execute(
                        delete(cls.model).where(cls.model.id == avatar.id)
                    )
                    deleted_uuids.append(avatar.uuid)
                
                await session.commit()
                return deleted_uuids 