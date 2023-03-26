"""Собственные классы исключения."""


class SendMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass


class EndpointStatusError(Exception):
    """API-сервер недоступен."""

    pass


class EndPointError(Exception):
    """Ошибка в доступе к ENDPOINT."""

    pass
