import abc
import dataclasses
from typing import Any, Callable

from tkursed import _consts

ValidationErrors = dict[str, Any]
"""The ValidationErrors type represents the results of a Tkursed State objects'
validate method and that of its children.

The actual type here is
    ValidationErrors: dict[str, ValueError|
                                "ValidationErrors"|
                                set[tuple[Any, Exception|"ValidationErrors"|set[...]]]]

Mypy does not yet support recursive types, unfortunately.
"""


class _TkursedState(abc.ABC):
    def __post_init__(self):
        errors = self.validate()
        if errors:
            raise ValueError("validation errors", errors)

    @abc.abstractmethod
    def validate(self) -> ValidationErrors:
        """validate returns a data structure with any Exceptions that
        mark the data as invalid.

        It is a recursive mapping containing one or more attribute names to Exceptions
        - or in the case of a collection or object, another data structure
        representing that child state object's errors.

        - Primitives are mapped to their Exceptions.
        - Sequence and Mapping types are recursively mapped to their children.
        - Set types are mapped to a set of tuples containing the value that
            had a validation error and the Exception or recursive structure
            describing the validation error.
        """
        raise NotImplementedError


@dataclasses.dataclass(slots=True)
class Dimensions(_TkursedState):
    width: int
    height: int

    @property
    def area(self):
        return self.width * self.height

    @property
    def area_rgba_bytes(self):
        return self.area * _consts.BPP // 8

    def as_tuple(self) -> tuple[int, int]:
        return (self.width, self.height)

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}
        if self.width <= 0:
            errors["width"] = ValueError("nonpositive width", self.width)
        if self.height <= 0:
            errors["height"] = ValueError("nonpositive height", self.height)

        return errors


@dataclasses.dataclass(slots=True)
class State(_TkursedState):
    canvas_dimensions: Dimensions = dataclasses.field(
        default_factory=lambda: Dimensions(800, 600)
    )

    pixel: tuple[int, int, int] = (0, 0, 0)

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}

        if child_errors := self.canvas_dimensions.validate():
            errors["canvas_dimensions"] = child_errors

        if any((v for v in self.pixel if not 0 <= v <= 255)):
            errors["pixel"] = ValueError(
                "pixel byte out of range 0<=value<=255", self.pixel
            )

        return errors


Reducer = Callable[[int, State], State | None]
