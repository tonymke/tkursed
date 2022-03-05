import PIL.Image
import PIL.ImageTk

from tkursed import _state


class Renderer:
    def __init__(self):
        self.__image: PIL.Image.Image
        self.__tk_image: PIL.ImageTk.PhotoImage

        self.__frame_buffer = bytearray()

    def __draw(self, dimensions: _state.Dimensions, needs_reinit: bool = False) -> None:
        if needs_reinit:
            self.__image = PIL.Image.frombuffer(
                "RGBA",
                dimensions.as_tuple(),  # mode  # size tuple
                self.__frame_buffer,  # data buffer
                "raw",  # decoder name
                "RGBA",  # decoder arg - mode
                0,  # decoder arg - stride (bits between pixels)
                1,  # decoder arg - orientation - up
            )
            self.__tk_image = PIL.ImageTk.PhotoImage(image=self.__image)
        else:
            self.__tk_image.paste(self.__image)

    @staticmethod
    def __resize_bytearray(desired_len: int, out_ba: bytearray) -> int:
        if desired_len < 0:
            raise ValueError("negative desired_len")

        current_len = len(out_ba)
        resize_amount = desired_len - current_len

        if resize_amount == 0:
            return 0

        if resize_amount > 0:
            out_ba[current_len:desired_len] = b"\x00" * resize_amount
        else:
            del out_ba[desired_len:]

        assert desired_len == len(
            out_ba
        ), f"resize mangled; desired {desired_len}, got {len(out_ba)}"

        return resize_amount

    def render(self, state: _state.State) -> PIL.ImageTk.PhotoImage | None:
        needs_reinit = bool(
            self.__resize_bytearray(
                state.canvas.dimensions.area_rgba_bytes,
                self.__frame_buffer,
            )
        )

        self.__frame_buffer[:] = (
            *state.canvas.background_color,
            255,
        ) * state.canvas.dimensions.area

        self.__draw(state.canvas.dimensions, needs_reinit)
        if needs_reinit:
            return self.__tk_image

        return None
