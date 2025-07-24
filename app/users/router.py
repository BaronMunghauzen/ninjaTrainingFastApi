from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Response, Depends
from app.users.auth import get_password_hash, authenticate_user, create_access_token, create_refresh_token
from app.users.dao import UsersDAO
from app.users.dependencies import get_current_user, get_current_admin_user, get_current_user_user
from app.users.models import User
from app.users.schemas import SUserRegister, SUserAuth, SUserUpdate

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post("/register/")
async def register_user(user_data: SUserRegister) -> dict:
    user = await UsersDAO.find_one_or_none(email=user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь уже существует'
        )
    
    # Проверяем, что логин тоже уникален
    user_by_login = await UsersDAO.find_one_or_none(login=user_data.login)
    if user_by_login:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Пользователь с таким логином уже существует'
        )
    
    user_dict = user_data.model_dump()
    user_dict['password'] = get_password_hash(user_data.password)
    
    # Устанавливаем значения по умолчанию только для обязательных полей
    user_dict['subscription_status'] = 'pending'
    user_dict['subscription_until'] = None
    user_dict['theme'] = 'dark'
    user_dict['is_user'] = True
    user_dict['is_admin'] = False
    
    # Создаем пользователя
    user_uuid = await UsersDAO.add(**user_dict)
    
    # Получаем созданного пользователя
    new_user = await UsersDAO.find_full_data(user_uuid)
    
    # Создаем токены для нового пользователя
    access_token = create_access_token({"sub": str(new_user.id)})
    refresh_token = create_refresh_token({"sub": str(new_user.id)})
    
    return {
        'message': 'Вы успешно зарегистрированы!',
        'access_token': access_token,
        'refresh_token': refresh_token
    }


@router.post("/login")
async def auth_user(response: Response, user_data: SUserAuth):
    check = await authenticate_user(user_identity=user_data.user_identity, password=user_data.password)
    if check is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Неверные данные для входа или пароль')
    access_token = create_access_token({"sub": str(check.id)})
    refresh_token = create_refresh_token({"sub": str(check.id)})
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return {'access_token': access_token, 'refresh_token': refresh_token}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)):
    return await user_data.to_dict()


@router.post("/logout/")
async def logout_user(response: Response):
    response.delete_cookie(key="users_access_token")
    return {'message': 'Пользователь успешно вышел из системы'}


@router.get("/all_users/")
async def get_all_users(user_data: User = Depends(get_current_admin_user)):
    return await UsersDAO.find_all()

@router.put("/update/{user_uuid}")
async def update_user(user_uuid: UUID, user: SUserUpdate, user_data: User = Depends(get_current_user_user)) -> dict:
    update_data = user.model_dump(exclude_unset=True)
    check = await UsersDAO.update(user_uuid, **update_data)
    if check:
        updated_user = await UsersDAO.find_full_data(user_uuid)
        return {
            "message": "Пользователь успешно обновлен!",
            "user": updated_user.to_dict()
        }
    else:
        return {"message": "Ошибка при обновлении пользователя!"}