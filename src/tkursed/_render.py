import PIL.Image
import PIL.ImageTk

from tkursed import _state


class Renderer:
    def __init__(self):
        self.__image: PIL.Image.Image
        self.__tk_image: PIL.ImageTk.PhotoImage

        self.__dimensions = (0, 0)
        self.__frame_buffer = bytearray()

    def __draw(
        self, dimensions: _state.Dimensions, new_frame_buffer: bytearray | None
    ) -> None:
        if new_frame_buffer:
            self.__frame_buffer = new_frame_buffer
            self.__image = PIL.Image.frombuffer(
                "RGBA",
                dimensions.as_tuple(),  # mode  # size tuple
                new_frame_buffer,  # data buffer
                "raw",  # decoder name
                "RGBA",  # decoder arg - mode
                0,  # decoder arg - stride (bits between pixels)
                1,  # decoder arg - orientation - up
            )
            self.__tk_image = PIL.ImageTk.PhotoImage(image=self.__image)
        else:
            self.__tk_image.paste(self.__image)

    def render(self, state: _state.State) -> PIL.ImageTk.PhotoImage | None:
        # bytearrays cannot be resized once exported to C. we need to alloc
        # a new one :-(
        if state.canvas.dimensions == self.__dimensions:
            frame_buffer = self.__frame_buffer
            new_frame_buffer = None
        else:
            frame_buffer = bytearray(state.canvas.dimensions.area_rgba_bytes)
            new_frame_buffer = frame_buffer
            self.__dimensions = state.canvas.dimensions.as_tuple()

        frame_buffer[:] = (
            *state.canvas.background_color,
            255,
        ) * state.canvas.dimensions.area

        self.__draw(state.canvas.dimensions, new_frame_buffer)
        if new_frame_buffer:
            return self.__tk_image

        return None
