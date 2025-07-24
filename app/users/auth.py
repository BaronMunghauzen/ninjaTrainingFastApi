from passlib.context import CryptContext

from jose import jwt
from datetime import datetime, timedelta, timezone

from pydantic import EmailStr

from app.config import get_auth_data
from app.users.dao import UsersDAO
from sqlalchemy import or_, select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=90)  # Refresh токен на 90 дней
    to_encode.update({"exp": expire})
    auth_data = get_auth_data()
    encode_jwt = jwt.encode(to_encode, auth_data['secret_key'], algorithm=auth_data['algorithm'])
    return encode_jwt


async def authenticate_user(user_identity: str, password: str):
    from app.users.models import User
    from app.database import async_session_maker
    async with async_session_maker() as session:
        stmt = select(User).where(
            or_(
                User.email == user_identity,
                User.login == user_identity,
                User.phone_number == user_identity
            )
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
    if not user or verify_password(plain_password=password, hashed_password=user.password) is False:
        return None
    return user
