from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.programs.dao import ProgramDAO
from app.programs.rb import RBProgram
from app.programs.schemas import SProgram, SProgramAdd, SProgramUpdate
from app.users.dependencies import get_current_admin_user, get_current_user_user
from app.categories.dao import CategoryDAO
from app.users.dao import UsersDAO
from app.files.dao import FilesDAO
from app.files.service import FileService

router = APIRouter(prefix='/programs', tags=['Работа с программами'])


@router.get("/", summary="Получить все программы")
async def get_all_programs(request_body: RBProgram = Depends(), user_data = Depends(get_current_user_user)) -> list[dict]:
    programs = await ProgramDAO.find_all(**request_body.to_dict())
    # Получаем все category_id и user_id из программ
    category_ids = {p.category_id for p in programs}
    user_ids = {p.user_id for p in programs if p.user_id is not None}
    categories = await CategoryDAO.find_in('id', list(category_ids)) if category_ids else []
    users = await UsersDAO.find_in('id', list(user_ids)) if user_ids else []
    id_to_category = {c.id: c.to_dict() for c in categories}
    id_to_user = {u.id: await u.to_dict() for u in users}
    result = []
    for p in programs:
        data = p.to_dict()
        # Удаляем id и uuid поля
        data.pop('category_id', None)
        data.pop('user_id', None)
        data.pop('category_uuid', None)
        data.pop('user_uuid', None)
        data.pop('schedule_type', None)
        # training_days теперь возвращаем
        # Добавляем вложенные объекты
        data['category'] = id_to_category.get(p.category_id)
        data['user'] = id_to_user.get(p.user_id) if p.user_id else None
        result.append(data)
    return result


@router.get("/{program_uuid}", summary="Получить одну программу по id")
async def get_program_by_id(program_uuid: UUID, user_data = Depends(get_current_user_user)) -> dict:
    rez = await ProgramDAO.find_full_data(program_uuid)
    if rez is None:
        return {'message': f'Программа с ID {program_uuid} не найдена!'}
    category = await CategoryDAO.find_one_or_none(id=rez.category_id)
    user = await UsersDAO.find_one_or_none(id=rez.user_id) if rez.user_id else None
    data = rez.to_dict()
    data.pop('category_id', None)
    data.pop('user_id', None)
    data.pop('category_uuid', None)
    data.pop('user_uuid', None)
    data.pop('schedule_type', None)
    # training_days теперь возвращаем
    data['category'] = category.to_dict() if category else None
    data['user'] = await user.to_dict() if user else None
    return data


@router.post("/add/")
async def add_program(program: SProgramAdd, user_data = Depends(get_current_admin_user)) -> dict:
    values = program.model_dump()
    # Получаем category_id по category_uuid
    category = await CategoryDAO.find_one_or_none(uuid=values.pop('category_uuid'))
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    values['category_id'] = category.id

    # Аналогично для user_uuid, если нужно
    user_id = None
    if values.get('user_uuid'):
        user = await UsersDAO.find_one_or_none(uuid=values['user_uuid'])
        if not user:
            # Удаляем user_uuid, даже если пользователь не найден
            values.pop('user_uuid', None)
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        user_id = user.id
    # Удаляем user_uuid в любом случае
    values.pop('user_uuid', None)
    values['user_id'] = user_id

    # Обработка image_uuid
    if values.get('image_uuid'):
        image = await FilesDAO.find_one_or_none(uuid=values.pop('image_uuid'))
        if not image:
            raise HTTPException(status_code=404, detail="Изображение не найдено")
        values['image_id'] = image.id
    # Удаляю image_uuid если вдруг остался
    values.pop('image_uuid', None)
    program_uuid = await ProgramDAO.add(**values)
    program_obj = await ProgramDAO.find_full_data(program_uuid)
    # Формируем ответ как в get_program_by_id
    category = await CategoryDAO.find_one_or_none(id=program_obj.category_id)
    user = await UsersDAO.find_one_or_none(id=program_obj.user_id) if program_obj.user_id else None
    data = program_obj.to_dict()
    data.pop('category_id', None)
    data.pop('user_id', None)
    data.pop('category_uuid', None)
    data.pop('user_uuid', None)
    data.pop('schedule_type', None)
    data.pop('training_days', None)
    data['category'] = category.to_dict() if category else None
    data['user'] = await user.to_dict() if user else None
    return data


@router.put("/update/{program_uuid}")
async def update_program(program_uuid: UUID, program: SProgramUpdate, user_data = Depends(get_current_admin_user)) -> dict:
    update_data = program.model_dump(exclude_unset=True)
    # Преобразуем category_uuid и user_uuid в id, если они есть
    if 'category_uuid' in update_data:
        category = await CategoryDAO.find_one_or_none(uuid=update_data.pop('category_uuid'))
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        update_data['category_id'] = category.id
    if 'user_uuid' in update_data:
        user = await UsersDAO.find_one_or_none(uuid=update_data.pop('user_uuid'))
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        update_data['user_id'] = user.id

    # Обработка image_uuid
    if 'image_uuid' in update_data:
        image_uuid = update_data.pop('image_uuid')
        if image_uuid:
            image = await FilesDAO.find_one_or_none(uuid=image_uuid)
            if not image:
                raise HTTPException(status_code=404, detail="Изображение не найдено")
            update_data['image_id'] = image.id
        else:
            update_data['image_id'] = None

    check = await ProgramDAO.update(program_uuid, **update_data)
    if check:
        updated_program = await ProgramDAO.find_full_data(program_uuid)
        category = await CategoryDAO.find_one_or_none(id=updated_program.category_id)
        user = await UsersDAO.find_one_or_none(id=updated_program.user_id) if updated_program.user_id else None
        data = updated_program.to_dict()
        data.pop('category_id', None)
        data.pop('user_id', None)
        data.pop('category_uuid', None)
        data.pop('user_uuid', None)
        data.pop('schedule_type', None)
        data.pop('training_days', None)
        data['category'] = category.to_dict() if category else None
        data['user'] = await user.to_dict() if user else None
        return data
    else:
        return {"message": "Ошибка при обновлении программы!"}


@router.delete("/delete/{program_uuid}")
async def delete_program_by_id(program_uuid: UUID, user_data = Depends(get_current_admin_user)) -> dict:
    check = await ProgramDAO.delete_by_id(program_uuid)
    if check:
        return {"message": f"Программа с ID {program_uuid} удалена!"}
    else:
        return {"message": "Ошибка при удалении программы!"}


@router.post("/{program_uuid}/upload-image", summary="Загрузить изображение для программы")
async def upload_program_image(
    program_uuid: UUID,
    file: UploadFile = File(...),
    user_data = Depends(get_current_admin_user)
):
    program = await ProgramDAO.find_full_data(program_uuid)
    if not program:
        raise HTTPException(status_code=404, detail="Программа не найдена")
    old_file_uuid = getattr(program.image, 'uuid', None)
    saved_file = await FileService.save_file(
        file=file,
        entity_type="program",
        entity_id=program.id,
        old_file_uuid=str(old_file_uuid) if old_file_uuid else None
    )
    await ProgramDAO.update(program_uuid, image_id=saved_file.id)
    return {"message": "Изображение успешно загружено", "image_uuid": saved_file.uuid}


@router.delete("/{program_uuid}/delete-image", summary="Удалить изображение программы")
async def delete_program_image(
    program_uuid: UUID,
    user_data = Depends(get_current_admin_user)
):
    program = await ProgramDAO.find_full_data(program_uuid)
    if not program:
        raise HTTPException(status_code=404, detail="Программа не найдена")
    
    if not program.image:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    
    image_uuid = program.image.uuid
    # Удаляем файл (это автоматически очистит image_id в programs и запись в files)
    try:
        await FileService.delete_file_by_uuid(str(image_uuid))
    except Exception as e:
        # Если удаление файла не удалось, возвращаем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении файла: {str(e)}")
    
    return {"message": "Изображение успешно удалено"}