from typing import Optional
from uuid import UUID

from fastapi import Request, HTTPException, status, Depends, Header
from jose import jwt, JWTError
from datetime import datetime, timezone
from app.config import get_auth_data
from app.exceptions import TokenExpiredException, NoJwtException, NoUserIdException, ForbiddenException
from app.users.dao import UsersDAO
from app.users.models import User
from app.trainings.dao import TrainingDAO
from app.anonymous_session.dao import AnonymousSessionDAO


def get_token(request: Request):
    token = request.cookies.get('users_access_token')
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not found')
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        auth_data = get_auth_data()
        payload = jwt.decode(token, auth_data['secret_key'], algorithms=[auth_data['algorithm']])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен не валидный!')

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Токен истек')

    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Не найден ID пользователя')

    user = await UsersDAO.find_one_or_none_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    if not user.actual:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Профиль деактивирован')

    return user


async def get_current_user_user(current_user: User = Depends(get_current_user)):
    if current_user.is_user:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')


async def get_optional_current_user_user(request: Request) -> Optional[User]:
    """
    Пользователь с ролью user, если в запросе есть валидный cookie users_access_token.
    Иначе None — без 401 (для публичных эндпоинтов вроде /public-training/*).
    """
    token = request.cookies.get("users_access_token")
    if not token:
        return None
    try:
        user = await get_current_user(token)
    except HTTPException:
        return None
    if not user.is_user:
        return None
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав!')


async def get_current_user_or_valid_anonymous_session(
    request: Request,
    anonymous_session_id: Optional[str] = Header(default=None, alias="anonymous_session_id"),
):
    """
    Доступ:
    1) обычный пользователь по токену (cookie users_access_token), либо
    2) анонимный доступ по заголовку anonymous_session_id, если сессия есть в таблице anonymous_session
       (actual=true) или есть связанные записи в trainings.
    """
    token = request.cookies.get("users_access_token")
    if token:
        # Если токен передан — работаем по обычной авторизации и не делаем fallback.
        return await get_current_user_user(await get_current_user(token))

    if not anonymous_session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found")

    try:
        anonymous_uuid = UUID(anonymous_session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid anonymous_session_id")

    if await AnonymousSessionDAO.exists_active(anonymous_uuid):
        return {"is_anonymous": True, "anonymous_session_id": str(anonymous_uuid)}

    trainings = await TrainingDAO.find_all(anonymous_session_id=str(anonymous_uuid))
    if not trainings:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Anonymous session not found")

    return {"is_anonymous": True, "anonymous_session_id": str(anonymous_uuid)}

