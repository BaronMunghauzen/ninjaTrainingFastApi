from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid4()), index=True)
    filename = Column(String, nullable=False)  # Оригинальное имя файла
    file_path = Column(String, nullable=False)  # Путь к файлу на сервере
    file_size = Column(Integer, nullable=False)  # Размер файла в байтах
    mime_type = Column(String, nullable=False)  # MIME тип файла
    entity_type = Column(String, nullable=False)  # Тип сущности (user, program, etc.)
    entity_id = Column(Integer, nullable=False)  # ID сущности
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # Внешний ключ к пользователю
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи с другими моделями (убираем связь user для избежания конфликтов)
    # user = relationship("User", back_populates="avatar", foreign_keys=[user_id]) 