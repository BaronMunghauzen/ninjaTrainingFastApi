from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base, str_uniq, int_pk, str_null_true, uuid_field
from datetime import date


# создаем модель таблицы категорий программ
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int_pk]
    uuid: Mapped[uuid_field]
    caption: Mapped[str_uniq]
    description: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int]

    # Определяем отношения: одна категория имеет несколько программ
    # Используем строковую ссылку для отношения
    programs: Mapped[list["Program"]] = relationship(
        "Program",
        back_populates="category"
    )


    def __str__(self):
        return (f"{self.__class__.__name__}(id={self.id}, "
                f"uuid={self.uuid!r},"
                f"caption={self.caption!r})")

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            "uuid": str(self.uuid),
            "caption": self.caption,
            "description": self.description,
            "order": self.order
        }