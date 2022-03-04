import dataclasses
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclasses.dataclass(slots=True)
class State:
    canvas_width: int = 800
    canvas_height: int = 600
    pixel: tuple[int, int, int] = (0, 0, 0)


Reducer = Callable[[int, State], State]
