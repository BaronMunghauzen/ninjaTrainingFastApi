from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    code = Column(String(6), nullable=False, index=True)  # 6-значный код
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связь с пользователем
    user = relationship("User", back_populates="password_reset_codes")

    def __repr__(self):
        return f"<PasswordResetCode(id={self.id}, user_id={self.user_id}, used={self.used})>"
