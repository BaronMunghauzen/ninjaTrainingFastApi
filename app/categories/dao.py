from uuid import UUID

from sqlalchemy import select, insert, update, event, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.categories.models import Category
from app.exceptions import CategotyNotFoundException


class CategoryDAO(BaseDAO):
    model = Category

    # @event.listens_for(Student, 'after_insert')
    # def receive_after_insert(mapper, connection, target):
    #     major_id = target.major_id
    #     connection.execute(
    #         update(Major)
    #         .where(Major.id == major_id)
    #         .values(count_students=Major.count_students + 1)
    #     )

    # @classmethod
    # async def add_category(cls, **student_data: dict):
    #     async with async_session_maker() as session:
    #         async with session.begin():
    #             new_student = Student(**student_data)
    #             session.add(new_student)
    #             await session.flush()
    #             new_student_uuid = new_student.uuid
    #             await session.commit()
    #             return new_student_uuid

    # @event.listens_for(Student, 'after_delete')
    # def receive_after_delete(mapper, connection, target):
    #     major_id = target.major_id
    #     connection.execute(
    #         update(Major)
    #         .where(Major.id == major_id)
    #         .values(count_students=Major.count_students - 1)
    #     )

