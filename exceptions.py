class EnvVariableError(Exception):
    """Отсутствие переменных окружения."""

    pass


class MissingKeyError(Exception):
    """Отсутствие ожидаемых ключей словаря."""

    pass


class UnexpectedStatusError(KeyError):
    """Неожиданный статус домашней работы."""

    pass


class APIUnavailableError(Exception):
    """Отсутствие доступа к API."""

    pass


class NotJSONResponseError(Exception):
    """Ответ API не в json формате."""

    pass
