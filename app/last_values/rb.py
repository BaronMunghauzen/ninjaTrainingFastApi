class RBLastValue:
    def __init__(self, 
                 uuid: str | None = None,
                 user_uuid: str | None = None,
                 name: str | None = None,
                 code: str | None = None,
                 actual: bool | None = None):
        self.uuid = uuid
        self.user_uuid = user_uuid
        self.name = name
        self.code = code
        self.actual = actual

    def to_dict(self) -> dict:
        data = {
            'uuid': self.uuid,
            'user_uuid': self.user_uuid,
            'name': self.name,
            'code': self.code,
            'actual': self.actual
        }
        # Фильтруем None значения
        filtered_data = {key: value for key, value in data.items() if value is not None}
        return filtered_data

