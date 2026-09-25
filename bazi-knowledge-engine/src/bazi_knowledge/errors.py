"""Typed input errors for clients; remains compatible with ValueError handlers."""


class PillarInputError(ValueError):
    def __init__(self, position: str, value: str, code: str, message: str):
        self.position = position
        self.value = value
        self.code = code
        super().__init__(f"{position}: {message}")
