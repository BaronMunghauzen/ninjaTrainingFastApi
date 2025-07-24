class RBCategory:
    def __init__(self, category_uuid: str | None = None,
                 caption: str | None = None,
                 description: str | None = None,
                 order: int | None = None):
        self.uuid = category_uuid
        self.caption = caption
        self.description = description
        self.order = order

    def to_dict(self) -> dict:
        data = {'uuid': self.uuid, 'caption': self.caption, 'description': self.description,
                'order': self.order}
        # Создаем копию словаря, чтобы избежать изменения словаря во время итерации
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data
