import abc
import copy
import dataclasses
import functools
import pathlib
from typing import Any, BinaryIO, ByteString, Final, TypeVar, Union

import PIL.Image

from tkursed import _consts, _image

FileOrPath = str | bytes | pathlib.Path | BinaryIO

T_VALIDATION_ERRORS = TypeVar("T_VALIDATION_ERRORS")
ValidationErrors = dict[
    str, ValueError | T_VALIDATION_ERRORS | set[tuple[Any, T_VALIDATION_ERRORS]]
]
"""The ValidationErrors type represents the results of a Tkursed State objects'
validate method and that of its children.
"""


class InvalidStateError(RuntimeError):
    def __init__(self, errors: ValidationErrors, msg: str = "runtime state is invalid"):
        super().__init__(msg, errors)


class BaseState(abc.ABC):
    __slots__: tuple[str, ...] = tuple()

    def __post_init__(self):
        # We use __post_init__ as most of our descendents are dataclasses
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
class Coordinates(BaseState):
    x: int
    y: int

    def __str__(self) -> str:
        return f"({self.x},{self.y})"

    def validate(self) -> ValidationErrors:
        return {}


@dataclasses.dataclass(slots=True)
class Dimensions(BaseState):
    width: int
    height: int

    @property
    def area(self):
        return self.width * self.height

    @property
    def area_rgba_bytes(self):
        return self.area * _consts.BPP // 8

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        if isinstance(other, Dimensions):
            return self.width == other.width and self.height == other.height

        if isinstance(other, tuple) and len(other) == 2:
            return self.width == other[0] and self.height == other[1]

        return False

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


RGBPixel = tuple[int, int, int]


def validate_RGBPixel(value: RGBPixel):
    errors: ValidationErrors = {}
    for i, pixel in enumerate(value):
        if not 0 <= pixel <= 255:
            errors[str(i)] = ValueError(
                "RGBPixel byte out of range 0<=X<=255", ("index", i), ("value", pixel)
            )

    return errors


T_IMAGE = TypeVar("T_IMAGE", bound="Image")
_IMAGE_DEFAULT_NAME: Final[str] = "(untitled)"


class Image(BaseState):
    __slots__ = ("__pixeldata", "__dimensions", "pixeldata", "__name")

    @property
    def dimensions(self) -> Dimensions:
        return self.__dimensions

    @property
    def name(self) -> str:
        return self.__name

    def __init__(
        self,
        image: PIL.Image.Image | FileOrPath,
        name: str = _IMAGE_DEFAULT_NAME,
    ) -> None:
        # image.load() reads in full, and closes any fds *that PIL itself opened*
        # https://pillow.readthedocs.io/en/stable/reference/open_files.html#image-lifecycle
        if isinstance(image, PIL.Image.Image):
            image.load()
        else:
            with PIL.Image.open(image) as image_:
                # closes any open FD *if PIL opened it*
                image = image_
                image.load()

        image = image.convert("RGBA")

        # getdata gives us a list of pixel tuples
        self.__pixeldata = functools.reduce(
            lambda acc, v: acc + bytes(v), image.getdata(), bytearray()
        )
        self.pixeldata = memoryview(self.__pixeldata).toreadonly()
        self.__dimensions = Dimensions(image.width, image.height)
        self.__name = name
        super().__post_init__()

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        if isinstance(other, Image):
            return (
                self.dimensions == other.dimensions
                and self.pixeldata == other.pixeldata
            )

        return False

    def __str__(self) -> str:
        return f"<image: {self.__name or _IMAGE_DEFAULT_NAME} {self.__dimensions}>"

    @classmethod
    def from_rgba_pixeldata(
        cls: type[T_IMAGE],
        data: ByteString,
        dimensions: Dimensions,
        name: str = _IMAGE_DEFAULT_NAME,
    ) -> T_IMAGE:
        pil_image = _image.rgba_bytes_to_PIL_image(data, dimensions.as_tuple())
        return cls(pil_image, name)

    def validate(self) -> ValidationErrors:
        # construction, readonly-ness ensures valid data
        return {}


_SPRITE_DEFAULT_NAME: Final[str] = "(untitled)"


class Sprite(BaseState):
    __slots__ = ("active_key", "images", "name")

    @property
    def active(self) -> Image:
        try:
            return self.images[self.active_key]
        except KeyError as ex:
            raise RuntimeError(
                "active_key not in images dict",
                ("active_key", self.active_key),
                ("images", self.images),
            ) from ex

    @active.setter
    def active(self, value: Image) -> None:
        new_active_key: str | None = next(
            (k for k, v in self.images.items() if v == value), None
        )
        if not new_active_key:
            raise ValueError(
                "value not in images dict' values",
                ("value", value),
                ("images", self.images),
            )

        self.active_key = new_active_key

    def __init__(
        self,
        images: Union[Image, dict[str, Image]],
        active_key: str = "",
        name: str = _SPRITE_DEFAULT_NAME,
    ) -> None:
        self.images: dict[str, Image]

        self.name = name
        if isinstance(images, Image):
            self.active_key = active_key
            self.images = {active_key: images}
        else:
            self.active_key = active_key
            self.images = images

        self.__post_init__()

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        if isinstance(other, Sprite):
            return (
                self.active_key == other.active_key
                and self.name == other.name
                and self.images == other.images
            )

        return False

    def __str__(self) -> str:
        return f"<sprite {self.name}>"

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}
        if len(self.images) == 0:
            errors["images"] = ValueError("empty images dict")
        if self.active_key not in self.images:
            errors["active_key"] = ValueError("active_key not in images dict keys")

        child_errors = {}
        for k, v in self.images.items():
            if err := v.validate():
                child_errors[k] = err

        if child_errors:
            errors["images"] = child_errors.copy()

        return errors


class PositionedSprite(Sprite):
    __slots__ = ("coordinates",)

    coordinates: Coordinates

    def __init__(
        self,
        images: Union[Image, dict[str, Image], Sprite],
        coordinates: Coordinates,
        active_key: str = "",
        name: str = _SPRITE_DEFAULT_NAME,
    ) -> None:
        if coordinates is None:
            coordinates = Coordinates(0, 0)
        self.coordinates = coordinates

        if isinstance(images, Sprite):
            super().__init__(copy.copy(images.images), images.active_key, images.name)
        else:
            super().__init__(images, active_key, name)

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True

        if isinstance(other, PositionedSprite):
            return self.coordinates == other.coordinates and super().__eq__(other)

        return False

    def __str__(self) -> str:
        return f"<sprite {self.name}@{self.coordinates}>"

    def validate(self) -> ValidationErrors:
        errors = super().validate()
        if child_error := self.coordinates.validate():
            errors["coordinates"] = child_error

        return errors


@dataclasses.dataclass(slots=True)
class Canvas(BaseState):
    background_color: RGBPixel = (0, 0, 0)
    dimensions: Dimensions = dataclasses.field(
        default_factory=lambda: Dimensions(800, 600)
    )
    sprites: list[PositionedSprite] = dataclasses.field(default_factory=list)

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}

        if child_errors := self.dimensions.validate():
            errors["dimensions"] = child_errors.copy()

        if child_errors := validate_RGBPixel(self.background_color):
            errors["background_color"] = child_errors.copy()

        if child_errors := dict(
            filter(
                lambda iv: iv[1],
                ((str(i), v.validate()) for i, v in enumerate(self.sprites)),
            )
        ):
            errors["sprites"] = dict(child_errors)

        return errors


@dataclasses.dataclass(slots=True)
class State(BaseState):
    canvas: Canvas = dataclasses.field(default_factory=Canvas)
    frame_rate: int = 0
    tick_rate_ms: int = 1000 // 60

    def validate(self) -> ValidationErrors:
        errors: ValidationErrors = {}

        if child_errors := self.canvas.validate():
            errors["canvas"] = child_errors.copy()

        if self.frame_rate < 0:
            errors["frame_rate"] = ValueError(
                "negative frame_rate", ("value", self.frame_rate)
            )

        if self.tick_rate_ms <= 0:
            errors["tick_rate_ms"] = ValueError(
                "nonpositive tick_rate_ms", ("value", self.tick_rate_ms)
            )

        return errors
