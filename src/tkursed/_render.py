import PIL.Image
import PIL.ImageTk

from tkursed import _consts, _state


class Image(PIL.ImageTk.PhotoImage):
    @property
    def _frame_buffer(self) -> bytearray:
        return self.__frame_buffer

    def __init__(self, width: int, height: int):
        if width <= 0:
            raise ValueError("non-positive width")

        if height <= 0:
            raise ValueError("non-positive height")

        self.__frame_buffer = bytearray(bytes((0, 0, 0, 255)) * width * height)
        self.__image = PIL.Image.frombuffer(
            "RGBA",
            (width, height),  # mode  # size tuple
            self.__frame_buffer,  # data buffer
            "raw",  # decoder name
            "RGBA",  # decoder arg - mode
            0,  # decoder arg - stride (bits between pixels)
            1,  # decoder arg - orientation - up
        )
        super().__init__(self.__image)

    def draw(self):
        frame_buffer_expected_size = self.width() * self.height() * _consts.BPP // 8
        if len(self.__frame_buffer) != frame_buffer_expected_size:
            raise RuntimeError("misshapen frame_buffer")

        self.paste(self.__image)


class Renderer:
    def __init__(self, image: Image):
        self.__image = image

    def render(self, state: _state.State) -> None:
        if len(state.pixel) + 1 != _consts.BPP // 8:
            raise RuntimeError("bad renderer state")

        self.__image._frame_buffer[:] = (
            bytes(
                (
                    *state.pixel,
                    255,
                )
            )
            * self.__image.width()
            * self.__image.height()
        )
        self.__image.draw()
