from uuid import uuid4, UUID
from sqlalchemy import UUID as SQLAlchemyUUID

from datetime import datetime, timezone
from typing import Annotated, AsyncGenerator


from sqlalchemy import func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column

from app.config import get_db_url

DATABASE_URL = get_db_url()

# Настройка пула соединений для оптимизации использования памяти
# pool_size - базовое количество соединений в пуле
# max_overflow - максимальное количество дополнительных соединений
# pool_pre_ping - проверка соединений перед использованием (предотвращает использование "мертвых" соединений)
# pool_recycle - пересоздание соединений каждые 3600 секунд (1 час) для предотвращения утечек
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,              # Максимум 5 соединений в пуле
    max_overflow=10,           # Дополнительно до 10 соединений (итого до 15)
    pool_pre_ping=True,        # Проверка соединений перед использованием
    pool_recycle=3600,         # Пересоздавать соединения каждый час
    echo=False                 # Отключить SQL логирование в продакшене
)
# expire_on_commit=True позволяет освобождать объекты из identity map после commit,
# что предотвращает накопление объектов в памяти и утечки памяти
async_session_maker = async_sessionmaker(engine, expire_on_commit=True)

# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True)]
uuid_field = Annotated[UUID, mapped_column(
    SQLAlchemyUUID(as_uuid=True),
    unique=True,
    nullable=False,
    default=uuid4,
    index=True
)]
created_at = Annotated[datetime, mapped_column(default=datetime.utcnow)]
updated_at = Annotated[datetime, mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
