from uuid import UUID
from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError

from app.user_measurements.dao import UserMeasurementDAO, UserMeasurementTypeDAO
from app.user_measurements.rb import RBUserMeasurement
from app.user_measurements.schemas import (
    SUserMeasurement, 
    SUserMeasurementAdd, 
    SUserMeasurementUpdate,
    SUserMeasurementResponse,
    SUserMeasurementListResponse,
    SUserMeasurementFilter
)
from app.users.dependencies import get_current_user_user
from app.users.models import User

router = APIRouter(prefix='/measurements', tags=['Измерения пользователей'])


@router.get("/", summary="Получить все измерения", response_model=List[SUserMeasurement])
async def get_all_measurements(
    request_body: RBUserMeasurement = Depends(),
    current_user: User = Depends(get_current_user_user)
) -> List[SUserMeasurement]:
    """Получить все измерения с фильтрацией"""
    measurements = await UserMeasurementDAO.find_all(**request_body.to_dict())
    return [SUserMeasurement.model_validate(m.to_dict()) for m in measurements]


@router.get("/user/", summary="Получить измерения пользователя с пагинацией", response_model=SUserMeasurementListResponse)
async def get_user_measurements(
    measurement_type_uuid: UUID = Query(None, description="Фильтр по типу измерения"),
    date_from: date = Query(None, description="Дата начала периода"),
    date_to: date = Query(None, description="Дата окончания периода"),
    actual: bool = Query(None, description="Фильтр по актуальности записи"),
    user_uuid: UUID = Query(None, description="Фильтр по UUID пользователя"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementListResponse:
    """Получить измерения пользователя с пагинацией и фильтрацией"""
    # Если передан user_uuid, используем его, иначе используем ID текущего пользователя
    target_user_id = current_user.id
    if user_uuid is not None:
        # Находим пользователя по UUID
        from app.users.dao import UsersDAO
        user = await UsersDAO.find_one_or_none(uuid=user_uuid)
        if user:
            target_user_id = user.id
    
    # Находим measurement_type_id если передан measurement_type_uuid
    measurement_type_id = None
    if measurement_type_uuid is not None:
        measurement_type = await UserMeasurementTypeDAO.find_one_or_none(uuid=measurement_type_uuid)
        if measurement_type:
            measurement_type_id = measurement_type.id
    
    result = await UserMeasurementDAO.find_by_user_with_pagination(
        user_id=target_user_id,
        page=page,
        size=size,
        measurement_type_id=measurement_type_id,
        date_from=date_from,
        date_to=date_to,
        actual=actual
    )
    
    measurements = [SUserMeasurement.model_validate(m.to_dict()) for m in result["items"]]
    
    return SUserMeasurementListResponse(
        items=measurements,
        pagination=result["pagination"]
    )


@router.get("/user/by-type/{measurement_type_uuid}", summary="Получить измерения пользователя по типу", response_model=List[SUserMeasurement])
async def get_user_measurements_by_type(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> List[SUserMeasurement]:
    """Получить все измерения пользователя определенного типа"""
    # Находим measurement_type_id по UUID
    measurement_type = await UserMeasurementTypeDAO.find_one_or_none(uuid=measurement_type_uuid)
    if not measurement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тип измерения не найден"
        )
    
    measurements = await UserMeasurementDAO.find_by_user_and_type(
        user_id=current_user.id,
        measurement_type_id=measurement_type.id
    )
    return [SUserMeasurement.model_validate(m.to_dict()) for m in measurements]


@router.get("/user/latest/{measurement_type_uuid}", summary="Получить последнее измерение пользователя по типу", response_model=SUserMeasurement)
async def get_latest_user_measurement_by_type(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurement:
    """Получить последнее измерение пользователя определенного типа"""
    # Находим measurement_type_id по UUID
    measurement_type = await UserMeasurementTypeDAO.find_one_or_none(uuid=measurement_type_uuid)
    if not measurement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тип измерения не найден"
        )
    
    measurement = await UserMeasurementDAO.find_latest_by_type(
        user_id=current_user.id,
        measurement_type_id=measurement_type.id
    )
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Измерения данного типа не найдены"
        )
    return SUserMeasurement.model_validate(measurement.to_dict())


@router.get("/{measurement_uuid}", summary="Получить измерение по UUID", response_model=SUserMeasurement)
async def get_measurement_by_uuid(
    measurement_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurement:
    """Получить измерение по UUID"""
    measurement = await UserMeasurementDAO.find_full_data(measurement_uuid)
    
    # Проверяем, что пользователь может просматривать только свои измерения
    if measurement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете просматривать только свои измерения"
        )
    
    return SUserMeasurement.model_validate(measurement.to_dict())


@router.post("/add/", summary="Добавить измерение", response_model=SUserMeasurementResponse)
async def add_measurement(
    measurement: SUserMeasurementAdd,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementResponse:
    """Добавить новое измерение"""
    try:
        # Используем user_uuid из запроса
        measurement_data = measurement.model_dump()
        
        measurement_uuid = await UserMeasurementDAO.add(**measurement_data)
        measurement_obj = await UserMeasurementDAO.find_full_data(measurement_uuid)
        
        return SUserMeasurementResponse(
            message="Измерение успешно добавлено!",
            measurement=SUserMeasurement.model_validate(measurement_obj.to_dict())
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при добавлении измерения"
        )


@router.put("/update/{measurement_uuid}", summary="Обновить измерение", response_model=SUserMeasurementResponse)
async def update_measurement(
    measurement_uuid: UUID,
    measurement: SUserMeasurementUpdate,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementResponse:
    """Обновить измерение"""
    # Проверяем, что пользователь может обновлять только свои измерения
    existing_measurement = await UserMeasurementDAO.find_full_data(measurement_uuid)
    if existing_measurement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете обновлять только свои измерения"
        )
    
    update_data = measurement.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления"
        )
    
    try:
        check = await UserMeasurementDAO.update(measurement_uuid, **update_data)
        if check:
            updated_measurement = await UserMeasurementDAO.find_full_data(measurement_uuid)
            return SUserMeasurementResponse(
                message="Измерение успешно обновлено!",
                measurement=SUserMeasurement.model_validate(updated_measurement.to_dict())
            )
        else:
            return SUserMeasurementResponse(
                message="Ошибка при обновлении измерения!",
                measurement=None
            )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при обновлении измерения"
        )


@router.delete("/delete/{measurement_uuid}", summary="Удалить измерение", response_model=dict)
async def delete_measurement(
    measurement_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Удалить измерение"""
    # Проверяем, что пользователь может удалять только свои измерения
    existing_measurement = await UserMeasurementDAO.find_full_data(measurement_uuid)
    if existing_measurement.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только свои измерения"
        )
    
    check = await UserMeasurementDAO.delete_by_id(measurement_uuid)
    if check:
        return {"message": f"Измерение с ID {measurement_uuid} удалено!"}
    else:
        return {"message": "Ошибка при удалении измерения!"}
