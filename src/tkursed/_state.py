import abc
import dataclasses
from typing import Callable


class _TkursedState(abc.ABC):
    def __post_init__(self):
        errors = self.validate()
        if errors:
            raise ValueError("validation errors", errors)

    @abc.abstractmethod
    def validate(self) -> dict[str, ValueError]:
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class State(_TkursedState):
    canvas_width: int = 800
    canvas_height: int = 600
    pixel: tuple[int, int, int] = (0, 0, 0)

    def validate(self) -> dict[str, ValueError]:
        errors: dict[str, ValueError] = {}
        if self.canvas_width <= 0:
            errors["canvas_width"] = ValueError(
                "nonpositive canvas_width", self.canvas_width
            )
        if self.canvas_height <= 0:
            errors["canvas_height"] = ValueError(
                "nonpositive canvas_height", self.canvas_height
            )

        if any((v for v in self.pixel if not 0 <= v <= 255)):
            errors["pixel"] = ValueError(
                "pixel byte out of range 0<=value<=255", self.pixel
            )

        return errors


Reducer = Callable[[int, State], State | None]
