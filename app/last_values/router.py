from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.last_values.dao import LastValueDAO
from app.last_values.rb import RBLastValue
from app.last_values.schemas import SLastValue, SLastValueAdd, SLastValueUpdate
from app.users.dependencies import get_current_user_user
from app.users.models import User

router = APIRouter(prefix='/last-values', tags=['Последние значения'])


@router.get("/", summary="Получить все последние значения")
async def get_all_last_values(
    request_body: RBLastValue = Depends(),
    current_user: User = Depends(get_current_user_user)
) -> list[SLastValue]:
    """Получение списка последних значений с фильтрацией (только для текущего пользователя)"""
    filters = request_body.to_dict()
    # Всегда фильтруем по текущему пользователю
    filters['user_uuid'] = str(current_user.uuid)
    values = await LastValueDAO.find_all(**filters)
    return [value.to_dict() for value in values]


@router.get("/{value_uuid}", summary="Получить одно значение по uuid")
async def get_last_value_by_uuid(
    value_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> SLastValue | dict:
    """Получение одного значения по UUID (только если оно принадлежит текущему пользователю)"""
    try:
        value = await LastValueDAO.find_full_data(value_uuid)
        # Проверяем, что значение принадлежит текущему пользователю
        if value.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
        return value.to_dict()
    except HTTPException as e:
        if e.status_code == 403:
            raise
        return {'message': f'Значение с ID {value_uuid} не найдено!'}


@router.post("/", summary="Создать или обновить значение по коду")
async def create_or_update_last_value(
    value_data: SLastValueAdd,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """
    Создание нового значения или обновление существующего по коду.
    Если запись с таким code и user_id существует, обновляет value и устанавливает actual=True.
    Пользователь может создавать записи только для себя (или админ для любого пользователя).
    """
    from app.users.dao import UsersDAO
    
    # Проверяем, что пользователь создает запись для себя или является админом
    if str(current_user.uuid) != str(value_data.user_uuid) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете создавать записи только для себя"
        )
    
    # Получаем пользователя по UUID
    target_user = await UsersDAO.find_full_data(value_data.user_uuid)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    value_uuid = await LastValueDAO.add_or_update_by_code(
        user_id=target_user.id,
        name=value_data.name,
        code=value_data.code,
        value=value_data.value
    )
    
    value_obj = await LastValueDAO.find_full_data(value_uuid)
    return {
        "message": "Значение успешно создано или обновлено!",
        "value": value_obj.to_dict()
    }


@router.put("/{value_uuid}", summary="Редактировать значение")
async def update_last_value(
    value_uuid: UUID,
    value_data: SLastValueUpdate,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Редактирование записи (только если она принадлежит текущему пользователю)"""
    # Проверяем, что значение принадлежит текущему пользователю
    try:
        value = await LastValueDAO.find_full_data(value_uuid)
        if value.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    except HTTPException as e:
        if e.status_code == 403:
            raise
        return {"message": f"Значение с ID {value_uuid} не найдено!"}
    
    update_data = value_data.model_dump(exclude_unset=True)
    
    check = await LastValueDAO.update(value_uuid, **update_data)
    if check:
        updated_value = await LastValueDAO.find_full_data(value_uuid)
        return {
            "message": "Значение успешно обновлено!",
            "value": updated_value.to_dict()
        }
    else:
        return {"message": "Ошибка при обновлении значения!"}


@router.delete("/{value_uuid}", summary="Удалить значение")
async def delete_last_value(
    value_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Удаление записи из базы данных (только если она принадлежит текущему пользователю)"""
    # Проверяем, что значение принадлежит текущему пользователю
    try:
        value = await LastValueDAO.find_full_data(value_uuid)
        if value.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    except HTTPException as e:
        if e.status_code == 403:
            raise
        return {"message": f"Значение с ID {value_uuid} не найдено!"}
    
    check = await LastValueDAO.delete_by_id(value_uuid)
    if check:
        return {"message": f"Значение с ID {value_uuid} удалено!"}
    else:
        return {"message": "Ошибка при удалении значения!"}


@router.delete("/{value_uuid}/deactivate", summary="Деактуализировать значение")
async def deactivate_last_value(
    value_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Деактуализация записи (установка actual=False) (только если она принадлежит текущему пользователю)"""
    # Проверяем, что значение принадлежит текущему пользователю
    try:
        value = await LastValueDAO.find_full_data(value_uuid)
        if value.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    except HTTPException as e:
        if e.status_code == 403:
            raise
        return {"message": f"Значение с ID {value_uuid} не найдено!"}
    
    check = await LastValueDAO.update(value_uuid, actual=False)
    if check:
        updated_value = await LastValueDAO.find_full_data(value_uuid)
        return {
            "message": "Значение успешно деактуализировано!",
            "value": updated_value.to_dict()
        }
    else:
        return {"message": "Ошибка при деактуализации значения!"}


@router.put("/{value_uuid}/activate", summary="Актуализировать значение")
async def activate_last_value(
    value_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Актуализация записи (установка actual=True) (только если она принадлежит текущему пользователю)"""
    # Проверяем, что значение принадлежит текущему пользователю
    try:
        value = await LastValueDAO.find_full_data(value_uuid)
        if value.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещен"
            )
    except HTTPException as e:
        if e.status_code == 403:
            raise
        return {"message": f"Значение с ID {value_uuid} не найдено!"}
    
    check = await LastValueDAO.update(value_uuid, actual=True)
    if check:
        updated_value = await LastValueDAO.find_full_data(value_uuid)
        return {
            "message": "Значение успешно актуализировано!",
            "value": updated_value.to_dict()
        }
    else:
        return {"message": "Ошибка при актуализации значения!"}

