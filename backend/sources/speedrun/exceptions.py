class SpeedrunError(RuntimeError):
    pass


class SpeedrunTimeoutError(SpeedrunError):
    pass


class SpeedrunHTTPError(SpeedrunError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Speedrun request failed with status {status_code}")


class SpeedrunProviderError(SpeedrunError):
    def __init__(self, code: str, message: str, status_code: int | None = None) -> None:
        self.code = code
        self.provider_message = message
        self.status_code = status_code
        super().__init__(f"Speedrun provider error {code}: {message}")


class SpeedrunResponseError(SpeedrunError):
    pass
