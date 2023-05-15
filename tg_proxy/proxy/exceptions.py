class BaseProxyException(Exception):
    code: int
    message: str

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class RequestEntityTooLargeException(BaseProxyException):
    pass


class NoMediaException(BaseProxyException):
    pass
