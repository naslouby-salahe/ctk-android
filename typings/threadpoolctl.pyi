from types import TracebackType
from typing import Self

class threadpool_limits:
    def __init__(self, limits: int | None = ..., user_api: str | None = ...) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
