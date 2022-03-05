import abc
import copy
import dataclasses
import pathlib
from typing import Any, BinaryIO, Callable, TypeVar

import PIL.Image

from tkursed import _consts

FileOrPath = str | bytes | pathlib.Path | BinaryIO

ValidationErrors = dict[str, Any]
"""The ValidationErrors type represents the results of a Tkursed State objects'
validate method and that of its children.

The actual type here is
    ValidationErrors: dict[str, ValueError|
                                "ValidationErrors"|
                                set[tuple[Any, Exception|"ValidationErrors"|set[...]]]]

Mypy does not yet support recursive types, unfortunately.
"""


class _BaseState(abc.ABC):
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
class Coordinates(_BaseState):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x},{self.y})"

    def validate(self) -> ValidationErrors:
        return {}


@dataclasses.dataclass(slots=True)
class Dimensions(_BaseState):
    width: int
    height: int

    @property
    def area(self):
        return self.width * self.height

    @property
    def area_rgba_bytes(self):
        return self.area * _consts.BPP // 8

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"

    def as_tuple(self) -> tuple[int, int]:
        return (self.width, self.height)

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}
        if self.width <= 0:
            errors["width"] = ValueError("nonpositive width", self.width)
        if self.height <= 0:
            errors["height"] = ValueError("nonpositive height", self.height)

        return errors


TImage = TypeVar("TImage", bound="Image")
_IMAGE_DEFAULT_NAME = "(untitled)"


class Image(_BaseState):
    __slots__ = ("__dimensions", "__rgba_pixel_data", "name")

    @property
    def dimensions(self) -> Dimensions:
        return copy.copy(self.__dimensions)

    def __init__(
        self,
        image: PIL.Image.Image | FileOrPath,
        name: str = _IMAGE_DEFAULT_NAME,
    ) -> None:
        concrete_image: PIL.Image.Image
        # mypy does not support match-case :-(
        if isinstance(image, PIL.Image.Image):
            concrete_image = image
        else:
            concrete_image = PIL.Image.open(image).convert("RGBA")

        self.__rgba_pixel_data = bytes(concrete_image.getdata())
        self.__dimensions = Dimensions(concrete_image.width, concrete_image.height)
        self.name = name
        super().__init__()
        super().__post_init__()

    def __bytes__(self) -> bytes:
        return memoryview(self.__rgba_pixel_data)

    def __str__(self) -> str:
        return f"<image: {self.name} {self.dimensions}>"

    def validate(self) -> ValidationErrors:
        # construction, readonly-ness ensures valid data
        return {}


@dataclasses.dataclass(slots=True)
class State(_BaseState):
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
