class TopStartupsError(RuntimeError):
    pass


class TopStartupsAccessError(TopStartupsError):
    pass


class TopStartupsHTTPError(TopStartupsError):
    def __init__(self, status_code: int | None = None) -> None:
        self.status_code = status_code
        message = "TopStartups request failed"
        if status_code is not None:
            message = f"{message} with status {status_code}"
        super().__init__(message)


class TopStartupsParseError(TopStartupsError):
    pass
