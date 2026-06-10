class KalshiError(Exception):
    pass

class KalshiHttpError(KalshiError):

    def __init__(self, status: int, message: str, code: str | None=None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code
