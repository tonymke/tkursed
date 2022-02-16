import sys
import tkinter
from tkinter import ttk
from typing import Callable, Union

import PIL.Image
import PIL.ImageTk

BPP = 32


def map_2d_coord_to_1d_index(two_dim_plane_width: int, x: int, y: int) -> int:
    return x + two_dim_plane_width * y


def map_1d_index_to_2d_coord(two_dim_plane_width: int, i: int) -> tuple[int, int]:
    return int(i % two_dim_plane_width), i // two_dim_plane_width


class Sprite:
    position_x: int
    position_y: int
    width: int
    height: int
    image: Union[bytes, bytearray]

    def __init__(
        self,
        image: Union[bytes, bytearray],
        position_x: int = 0,
        position_y: int = 0,
        width: int = 1,
        height: int = 1,
    ):
        if position_x < 0 or position_y < 0 or width < 1 or height < 1:
            raise ValueError("position/width out of bounds")

        if not image:
            raise ValueError("image data is required")

        if len(image) != height * width * (BPP // 8):
            raise ValueError("binary image has improper length")

        self.position_x = position_x
        self.position_y = position_y
        self.width = width
        self.height = height
        self.image = image


class TkursedRenderer:
    _tk_root: tkinter.Tk
    _tk_frame: ttk.Frame
    _image: PIL.Image
    _image_widget: PIL.ImageTk.PhotoImage
    _image_label: ttk.Label

    _bg_color: bytes
    _frame_buffer: bytearray
    _height: int
    _running: bool
    _title: str
    _user_loop_callback: Callable[[Callable[[], None]], None]
    _width: int

    _sprites: list[Sprite]

    @property
    def bg_color(self) -> bytes:
        return self._bg_color

    @property
    def height(self) -> int:
        return self._height

    @property
    def sprites(self) -> list[Sprite]:
        return self._sprites

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value:
            raise ValueError

        self._tk_root.title(value)
        self._title = value

    @property
    def width(self) -> int:
        return self._width

    def __init__(
        self,
        loop_callback: Callable[[Callable[[], None]], None],
        sprites: list[Sprite] = None,
        width: int = 800,
        height: int = 600,
        title: str = "A tcl/tk-ursed 2D Renderer",
        bg_color: bytes = b"\x00\x00\x00\xFF",
    ) -> None:
        if (
            width <= 0
            or height <= 0
            or not title
            or not loop_callback
            or len(bg_color) != 4
        ):
            raise ValueError

        self._width = width
        self._height = height
        self._running = False
        self._user_loop_callback = loop_callback  # type: ignore
        self._bg_color = bg_color
        self._frame_buffer = bytearray(self.bg_color * self.width * self.height)
        self._sprites = [] if not sprites else sprites

        self._tk_root = tkinter.Tk()
        self.title = title
        self._tk_root.columnconfigure(0, weight=1)
        self._tk_root.rowconfigure(0, weight=1)
        self._tk_root.resizable(False, False)

        self._tk_frame = ttk.Frame(
            self._tk_root, width=self._width, height=self._height
        )
        self._tk_frame.grid(
            column=0, row=0, sticky=tkinter.N + tkinter.W + tkinter.E + tkinter.S
        )
        self._tk_frame.pack()

        self._image = PIL.Image.frombuffer(
            "RGBA",  # mode
            (self.width, self.height),  # size tuple
            self._frame_buffer,  # data buffer
            "raw",  # decoder name
            "RGBA",  # decoder arg - mode
            0,  # decoder arg - stride
            1,  # decoder arg - orientation
        )
        self._image_widget = PIL.ImageTk.PhotoImage(self._image)
        self._image_label = ttk.Label(self._tk_frame, image=self._image_widget)
        self._image_label.pack()

    def _draw(self) -> None:
        self._frame_buffer[:] = self._bg_color * self.width * self.height
        # TODO draw sprites into buffer

        # There is no direct access to the image widget's underlying buffer. Enjoy.
        self._image_widget.paste(self._image)

    def _draw_sprite(self, sprite: Sprite) -> None:
        # skip if not on plane at all
        if sprite.position_x > self.width or sprite.position_y > self.height:
            return

        raise NotImplementedError

    def _main_loop(self) -> None:
        if not self._running:
            try:
                self._tk_root.destroy()
            except Exception:
                pass
            return

        try:
            self._user_loop_callback(self._draw)  # type: ignore
            self._tk_root.after(3, self._main_loop)
        except Exception:
            self._running = False
            try:
                self._tk_root.destroy()
            except Exception:
                pass
            raise

    def run(self) -> None:
        if self._running:
            raise RuntimeError("already running")

        try:
            # queue first draw in tk eventloop, start underlying mainloop
            self._running = True
            self._tk_root.after(1, self._main_loop)
            # blocks until window close or fatal exception
            self._tk_root.mainloop()
        finally:
            self._running = False


def main() -> int:
    TkursedRenderer(lambda draw_fn: draw_fn()).run()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
