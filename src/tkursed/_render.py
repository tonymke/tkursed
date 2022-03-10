from typing import NamedTuple

import PIL.Image
import PIL.ImageTk

from tkursed import _consts, _image, _state


class Renderer:
    __slots__ = (
        "__bg_cache",
        "__dimensions",
        "__frame_buffer",
        "__image",
        "__tk_image",
    )

    def __init__(self):
        self.__image: PIL.Image.Image
        self.__tk_image: PIL.ImageTk.PhotoImage
        self.__dimensions = (0, 0)
        self.__frame_buffer = bytearray()
        self.__bg_cache = bytes()

    def __bytes__(self) -> bytes:
        return bytes(self.__frame_buffer)

    def __draw(
        self, dimensions: _state.Dimensions, new_frame_buffer: bytearray | None
    ) -> None:
        if new_frame_buffer:
            self.__frame_buffer = new_frame_buffer
            self.__image = _image.rgba_bytes_to_PIL_image(
                self.__frame_buffer,
                dimensions.as_tuple(),
            )
            self.__tk_image = PIL.ImageTk.PhotoImage(image=self.__image)
        else:
            self.__tk_image.paste(self.__image)

    def render(self, state: _state.State) -> PIL.ImageTk.PhotoImage | None:
        # bytearrays cannot be resized once exported to C. we need to alloc
        # a new one :-(
        need_new_bg_cache = (
            not self.__bg_cache or state.canvas.background_color != self.__bg_cache[:3]
        )
        if state.canvas.dimensions == self.__dimensions:
            frame_buffer = self.__frame_buffer
            new_frame_buffer = None
        else:
            frame_buffer = bytearray(state.canvas.dimensions.area_rgba_bytes)
            new_frame_buffer = frame_buffer
            self.__dimensions = state.canvas.dimensions.as_tuple()
            need_new_bg_cache = True

        if need_new_bg_cache:
            self.__bg_cache = (
                bytes((*state.canvas.background_color, 255))
                * state.canvas.dimensions.area
            )

        # draw background
        frame_buffer[:] = self.__bg_cache

        # draw sprites
        for sprite in state.canvas.sprites:
            _render_visible_rows(sprite, state.canvas.dimensions, frame_buffer)

        self.__draw(state.canvas.dimensions, new_frame_buffer)
        if new_frame_buffer:
            return self.__tk_image

        return None


class _DimensionCropWindow(NamedTuple):
    """_DimensionCropWindow describes what portions of the sprite should be rendered
    and where."""

    coord: int
    """coord is the first coordinate in the sprite's image that will be visibile on the
    canvas, relative the sprite image's origin."""

    dimension_size: int
    """dimension_size is the number of pixels from the coord that will be visible on the
    canvas."""

    canvas_coord: int
    """canvas_coord is the position of coord relative to the canvas origin."""


def _crop_to_visible_for_dimension(
    canvas_coord: int, dimension_size: int, canvas_dimension_size: int
) -> _DimensionCropWindow | None:
    window_coord: int = 0
    window_dimension_size: int = dimension_size
    window_canvas_coord: int = canvas_coord

    # partially left/above canvas
    if canvas_coord < 0:
        # entirely off screen
        if canvas_coord + dimension_size <= 0:
            return None
        window_dimension_size = dimension_size - abs(canvas_coord)
        window_coord = dimension_size - window_dimension_size
        window_canvas_coord = 0
    # partially right/below canvas
    elif canvas_coord + dimension_size >= canvas_dimension_size:
        # entirely off screen
        if canvas_coord >= canvas_dimension_size:
            return None
        window_coord = 0
        window_dimension_size = canvas_dimension_size - canvas_coord
        window_canvas_coord = canvas_coord

    return _DimensionCropWindow(
        window_coord, window_dimension_size, window_canvas_coord
    )


# https://softwareengineering.stackexchange.com/a/212813
def _map_2d_coord_to_1d_index(two_dim_plane_width: int, x: int, y: int) -> int:
    return x + two_dim_plane_width * y


def _render_visible_rows(
    sprite: _state.PositionedSprite,
    canvas_dimensions: _state.Dimensions,
    frame_buffer: bytearray,
) -> None:
    image = sprite.active
    x_crop = _crop_to_visible_for_dimension(
        sprite.coordinates.x, image.dimensions.width, canvas_dimensions.width
    )
    y_crop = _crop_to_visible_for_dimension(
        sprite.coordinates.y, image.dimensions.height, canvas_dimensions.height
    )

    if not x_crop or not y_crop:
        # image not visible
        return

    sprite_i = (
        _map_2d_coord_to_1d_index(image.dimensions.width, x_crop.coord, y_crop.coord)
        * _consts.BPP
        // 8
    )
    canvas_i = (
        _map_2d_coord_to_1d_index(
            canvas_dimensions.width, x_crop.canvas_coord, y_crop.canvas_coord
        )
        * _consts.BPP
        // 8
    )

    sprite_width_bytes = image.dimensions.width * _consts.BPP // 8
    sprite_window_width_bytes = x_crop.dimension_size * _consts.BPP // 8
    canvas_width_bytes = canvas_dimensions.width * _consts.BPP // 8
    for row in range(y_crop.dimension_size):
        if row > 0:
            sprite_i += sprite_width_bytes
            canvas_i += canvas_width_bytes

        frame_buffer[canvas_i : canvas_i + sprite_window_width_bytes] = image.pixeldata[
            sprite_i : sprite_i + sprite_window_width_bytes
        ]
