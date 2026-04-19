from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.training_composition_rules.dao import TrainingCompositionRuleDAO
from app.training_composition_rules.filters import training_composition_rule_filters
from app.training_composition_rules.schemas import (
    STrainingCompositionRule,
    STrainingCompositionRuleAdd,
    STrainingCompositionRuleUpdate,
)
from app.users.dependencies import get_current_user_user

router = APIRouter(prefix="/training-composition-rules", tags=["Правила состава тренировок"])


@router.get("/", summary="Получить правила (опциональные фильтры по полям таблицы)")
async def get_all_rules(
    filters: dict = Depends(training_composition_rule_filters),
    user_data=Depends(get_current_user_user),
) -> list:
    items = await TrainingCompositionRuleDAO.find_all(**filters)
    return [STrainingCompositionRule.model_validate(r) for r in items]


@router.get("/{rule_uuid}", summary="Получить правило по uuid")
async def get_rule_by_uuid(rule_uuid: UUID, user_data=Depends(get_current_user_user)):
    try:
        item = await TrainingCompositionRuleDAO.find_full_data(rule_uuid)
        return STrainingCompositionRule.model_validate(item)
    except HTTPException as e:
        if e.status_code == 404:
            return {"message": f"Правило с uuid {rule_uuid} не найдено!"}
        raise


@router.post("/add/", summary="Создать правило")
async def add_rule(body: STrainingCompositionRuleAdd, user_data=Depends(get_current_user_user)):
    values = body.model_dump()
    rule_uuid = await TrainingCompositionRuleDAO.add(**values)
    item = await TrainingCompositionRuleDAO.find_full_data(rule_uuid)
    return {"message": "Правило создано", "uuid": str(rule_uuid), "rule": STrainingCompositionRule.model_validate(item)}


@router.put("/update/{rule_uuid}", summary="Обновить правило")
async def update_rule(rule_uuid: UUID, body: STrainingCompositionRuleUpdate, user_data=Depends(get_current_user_user)):
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    await TrainingCompositionRuleDAO.update(rule_uuid, **values)
    item = await TrainingCompositionRuleDAO.find_full_data(rule_uuid)
    return {"message": "Правило обновлено", "rule": STrainingCompositionRule.model_validate(item)}


@router.delete("/delete/{rule_uuid}", summary="Удалить правило")
async def delete_rule(rule_uuid: UUID, user_data=Depends(get_current_user_user)):
    await TrainingCompositionRuleDAO.delete_by_id(rule_uuid)
    return {"message": f"Правило {rule_uuid} удалено"}
