from uuid import UUID

from fastapi import APIRouter, Depends
from app.categories.dao import CategoryDAO
from app.categories.rb import RBCategory
from app.categories.schemas import SCategory, SCategoryAdd, SCategoryUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user

router = APIRouter(prefix='/categories', tags=['Работа с категориями'])


@router.get("/", summary="Получить все категории")
async def get_all_categories(request_body: RBCategory = Depends(), user_data = Depends(get_current_user_user)) -> list[SCategory]:
    return await CategoryDAO.find_all(**request_body.to_dict())


@router.get("/{category_uuid}", summary="Получить одну категорию по id")
async def get_category_by_id(category_uuid: UUID, user_data = Depends(get_current_user_user)) -> SCategory | dict:
    rez = await CategoryDAO.find_full_data(category_uuid)
    if rez is None:
        return {'message': f'Категория с ID {category_uuid} не найдена!'}
    return rez


@router.post("/add/")
async def add_category(category: SCategoryAdd, user_data = Depends(get_current_admin_user)) -> SCategory | dict:
    category_uuid = await CategoryDAO.add(**category.model_dump())
    if category:
        category_obj = await CategoryDAO.find_full_data(category_uuid)
        category_info = category_obj.to_dict()  # Вызываем to_dict() на объекте, а не корутине
        return {"message": "Категория успешно добавлена!", "category": category_info}
    else:
        return {"message": "Ошибка при добавлении категории!"}

@router.put("/update/{category_uuid}")
async def update_category(category_uuid: UUID, category: SCategoryUpdate, user_data = Depends(get_current_admin_user)) -> dict:
    # Преобразуем модель в dict, исключая None значения
    update_data = category.model_dump(exclude_unset=True)

    check = await CategoryDAO.update(category_uuid,
                                    **update_data)
    if check:
        updated_category = await CategoryDAO.find_full_data(category_uuid)
        return {
            "message": "Категория успешно обновлена!",
            "category": updated_category.to_dict()
        }
    else:
        return {"message": "Ошибка при обновлении категории!"}



@router.delete("/delete/{category_uuid}")
async def delete_category_by_id(category_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await CategoryDAO.delete_by_id(category_uuid)
    if check:
        return {"message": f"Категория с ID {category_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении категории!"}