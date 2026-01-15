from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError

from app.user_measurements.dao import UserMeasurementTypeDAO
from app.user_measurements.rb import RBUserMeasurementType
from app.user_measurements.schemas import (
    SUserMeasurementType, 
    SUserMeasurementTypeAdd, 
    SUserMeasurementTypeUpdate,
    SUserMeasurementTypeResponse,
    SUserMeasurementTypeListResponse,
    SArchiveRequest
)
from app.users.dependencies import get_current_user_user
from app.users.models import User

router = APIRouter(prefix='/measurement-types', tags=['Типы измерений пользователей'])


@router.get("/", summary="Получить все типы измерений", response_model=List[SUserMeasurementType])
async def get_all_measurement_types(
    request_body: RBUserMeasurementType = Depends(),
    current_user: User = Depends(get_current_user_user)
) -> List[SUserMeasurementType]:
    """Получить все типы измерений с фильтрацией"""
    measurement_types = await UserMeasurementTypeDAO.find_all(**request_body.to_dict())
    return [SUserMeasurementType.model_validate(mt.to_dict()) for mt in measurement_types]


@router.get("/system/", summary="Получить системные типы измерений", response_model=List[SUserMeasurementType])
async def get_system_measurement_types(
    current_user: User = Depends(get_current_user_user)
) -> List[SUserMeasurementType]:
    """Получить все системные типы измерений"""
    measurement_types = await UserMeasurementTypeDAO.find_system_types()
    return [SUserMeasurementType.model_validate(mt.to_dict()) for mt in measurement_types]


@router.get("/user/", summary="Получить пользовательские типы измерений", response_model=List[SUserMeasurementType])
async def get_user_measurement_types(
    current_user: User = Depends(get_current_user_user)
) -> List[SUserMeasurementType]:
    """Получить все пользовательские типы измерений для текущего пользователя"""
    measurement_types = await UserMeasurementTypeDAO.find_user_types(current_user.id)
    return [SUserMeasurementType.model_validate(mt.to_dict()) for mt in measurement_types]


@router.get("/{measurement_type_uuid}", summary="Получить тип измерения по UUID", response_model=SUserMeasurementType)
async def get_measurement_type_by_uuid(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementType:
    """Получить тип измерения по UUID"""
    measurement_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    return SUserMeasurementType.model_validate(measurement_type.to_dict())


@router.post("/add/", summary="Добавить тип измерения", response_model=SUserMeasurementTypeResponse)
async def add_measurement_type(
    measurement_type: SUserMeasurementTypeAdd,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementTypeResponse:
    """Добавить новый тип измерения. Если запись с таким названием существует с actual=False, она будет восстановлена."""
    # Используем user_uuid из запроса
    measurement_type_data = measurement_type.model_dump()
    
    measurement_type_uuid = await UserMeasurementTypeDAO.add(**measurement_type_data)
    measurement_type_obj = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    
    return SUserMeasurementTypeResponse(
        message="Тип измерения успешно добавлен!",
        measurement_type=SUserMeasurementType.model_validate(measurement_type_obj.to_dict())
    )


@router.put("/update/{measurement_type_uuid}", summary="Обновить тип измерения", response_model=SUserMeasurementTypeResponse)
async def update_measurement_type(
    measurement_type_uuid: UUID,
    measurement_type: SUserMeasurementTypeUpdate,
    current_user: User = Depends(get_current_user_user)
) -> SUserMeasurementTypeResponse:
    """Обновить тип измерения"""
    # Проверяем, что пользователь может обновлять только свои типы измерений
    existing_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    if existing_type.data_type == "custom" and existing_type.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете обновлять только свои типы измерений"
        )
    
    update_data = measurement_type.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет данных для обновления"
        )
    
    try:
        check = await UserMeasurementTypeDAO.update(measurement_type_uuid, **update_data)
        if check:
            updated_measurement_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
            return SUserMeasurementTypeResponse(
                message="Тип измерения успешно обновлен!",
                measurement_type=SUserMeasurementType.model_validate(updated_measurement_type.to_dict())
            )
        else:
            return SUserMeasurementTypeResponse(
                message="Ошибка при обновлении типа измерения!",
                measurement_type=None
            )
    except IntegrityError as e:
        if "uq_measurement_type_caption_user" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Тип измерения с таким названием уже существует для данного пользователя"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при обновлении типа измерения"
        )


@router.delete("/delete/{measurement_type_uuid}", summary="Удалить тип измерения", response_model=dict)
async def delete_measurement_type(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Удалить тип измерения (вместе с связанными измерениями)"""
    # Проверяем, что пользователь может удалять только свои типы измерений
    existing_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    if existing_type.data_type == "custom" and existing_type.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять только свои типы измерений"
        )
    
    check = await UserMeasurementTypeDAO.delete_with_measurements(measurement_type_uuid)
    if check:
        return {"message": f"Тип измерения с ID {measurement_type_uuid} удален вместе с связанными измерениями!"}
    else:
        return {"message": "Ошибка при удалении типа измерения!"}


@router.post("/archive/{measurement_type_uuid}", summary="Архивировать тип измерения", response_model=dict)
async def archive_measurement_type(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Архивировать тип измерения (установить actual = False)"""
    # Проверяем, что пользователь может архивировать только свои типы измерений
    existing_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    if existing_type.data_type == "custom" and existing_type.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете архивировать только свои типы измерений"
        )
    
    check = await UserMeasurementTypeDAO.archive(measurement_type_uuid)
    if check:
        return {"message": f"Тип измерения с ID {measurement_type_uuid} архивирован!"}
    else:
        return {"message": "Ошибка при архивации типа измерения!"}


@router.post("/unarchive/{measurement_type_uuid}", summary="Разархивировать тип измерения", response_model=dict)
async def unarchive_measurement_type(
    measurement_type_uuid: UUID,
    current_user: User = Depends(get_current_user_user)
) -> dict:
    """Разархивировать тип измерения (установить actual = True)"""
    # Проверяем, что пользователь может разархивировать только свои типы измерений
    existing_type = await UserMeasurementTypeDAO.find_full_data(measurement_type_uuid)
    if existing_type.data_type == "custom" and existing_type.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете разархивировать только свои типы измерений"
        )
    
    check = await UserMeasurementTypeDAO.unarchive(measurement_type_uuid)
    if check:
        return {"message": f"Тип измерения с ID {measurement_type_uuid} разархивирован!"}
    else:
        return {"message": "Ошибка при разархивации типа измерения!"}
