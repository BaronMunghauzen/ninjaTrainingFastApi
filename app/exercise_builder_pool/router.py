from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.exercise_builder_pool.dao import ExerciseBuilderPoolDAO
from app.exercise_builder_pool.schemas import SExerciseBuilderPool, SExerciseBuilderPoolAdd, SExerciseBuilderPoolUpdate
from app.users.dependencies import get_current_user_user

router = APIRouter(prefix="/exercise-builder-pool", tags=["Пул упражнений для сборки тренировок"])


@router.get("/", summary="Получить все записи пула")
async def get_all(user_data=Depends(get_current_user_user)) -> list:
    items = await ExerciseBuilderPoolDAO.find_all()
    return [SExerciseBuilderPool.model_validate(r) for r in items]


@router.get("/{item_uuid}", summary="Получить запись по uuid")
async def get_by_uuid(item_uuid: UUID, user_data=Depends(get_current_user_user)):
    try:
        item = await ExerciseBuilderPoolDAO.find_full_data(item_uuid)
        return SExerciseBuilderPool.model_validate(item)
    except HTTPException as e:
        if e.status_code == 404:
            return {"message": f"Запись с uuid {item_uuid} не найдена!"}
        raise


@router.post("/add/", summary="Добавить запись")
async def add(body: SExerciseBuilderPoolAdd, user_data=Depends(get_current_user_user)):
    values = body.model_dump()
    item_uuid = await ExerciseBuilderPoolDAO.add(**values)
    item = await ExerciseBuilderPoolDAO.find_full_data(item_uuid)
    return {"message": "Запись создана", "uuid": str(item_uuid), "item": SExerciseBuilderPool.model_validate(item)}


@router.put("/update/{item_uuid}", summary="Обновить запись")
async def update(item_uuid: UUID, body: SExerciseBuilderPoolUpdate, user_data=Depends(get_current_user_user)):
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    await ExerciseBuilderPoolDAO.update(item_uuid, **values)
    item = await ExerciseBuilderPoolDAO.find_full_data(item_uuid)
    return {"message": "Запись обновлена", "item": SExerciseBuilderPool.model_validate(item)}


@router.delete("/delete/{item_uuid}", summary="Удалить запись")
async def delete(item_uuid: UUID, user_data=Depends(get_current_user_user)):
    await ExerciseBuilderPoolDAO.delete_by_id(item_uuid)
    return {"message": f"Запись {item_uuid} удалена"}
