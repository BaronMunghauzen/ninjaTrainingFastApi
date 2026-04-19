from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.user_selected_trainings.dao import UserSelectedTrainingDAO
from app.user_selected_trainings.schemas import (
    SUserSelectedTraining,
    SUserSelectedTrainingAdd,
    SUserSelectedTrainingUpdate,
)
from app.users.dependencies import get_current_user_user

router = APIRouter(prefix="/user-selected-trainings", tags=["Выбранные тренировки пользователя"])


@router.post("/add/", summary="Добавить тренировку для отображения")
async def add_user_selected_training(
    body: SUserSelectedTrainingAdd,
    user_data=Depends(get_current_user_user),
):
    values = body.model_dump()
    values["user_uuid"] = str(user_data.uuid)
    object_uuid = await UserSelectedTrainingDAO.add(**values)
    item = await UserSelectedTrainingDAO.find_full_data(object_uuid)
    return {
        "message": "Тренировка добавлена для отображения",
        "uuid": str(object_uuid),
        "item": SUserSelectedTraining.model_validate(item),
    }


@router.get("/", summary="Получить выбранные тренировки текущего пользователя")
async def get_my_selected_trainings(
    actual: Optional[bool] = Query(
        None,
        description="Если указано — фильтр по полю actual (показ на фронте)",
    ),
    user_data=Depends(get_current_user_user),
):
    filters: dict = {"user_uuid": str(user_data.uuid)}
    if actual is not None:
        filters["actual"] = actual
    items = await UserSelectedTrainingDAO.find_all(**filters)
    return [SUserSelectedTraining.model_validate(i) for i in items]


@router.get("/{object_uuid}", summary="Получить запись по UUID")
async def get_selected_training_by_uuid(object_uuid: UUID, user_data=Depends(get_current_user_user)):
    item = await UserSelectedTrainingDAO.find_one_or_none(uuid=object_uuid)
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if item.user_id != user_data.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    item = await UserSelectedTrainingDAO.find_full_data(object_uuid)
    return SUserSelectedTraining.model_validate(item)


@router.put("/update/{object_uuid}", summary="Обновить запись")
async def update_selected_training(
    object_uuid: UUID,
    body: SUserSelectedTrainingUpdate,
    user_data=Depends(get_current_user_user),
):
    item = await UserSelectedTrainingDAO.find_one_or_none(uuid=object_uuid)
    if not item:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    if item.user_id != user_data.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    await UserSelectedTrainingDAO.update(object_uuid, **values)

    updated = await UserSelectedTrainingDAO.find_full_data(object_uuid)
    return {"message": "Запись обновлена", "item": SUserSelectedTraining.model_validate(updated)}


@router.delete("/delete/{training_uuid}", summary="Удалить выбор тренировки по UUID тренировки")
async def delete_selected_training(training_uuid: UUID, user_data=Depends(get_current_user_user)):
    await UserSelectedTrainingDAO.delete_for_user_by_training_uuid(user_data.id, training_uuid)
    return {"message": f"Выбор тренировки {training_uuid} удалён"}
