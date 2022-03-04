import copy
import tkinter
import tkinter.ttk
from typing import TypeVar, cast

from tkursed import _render
from tkursed._state import Reducer, State

T = TypeVar("T")


class Tkursed(tkinter.ttk.Frame):
    def __init__(
        self,
        *args,
        reducer: Reducer,
        width: int = 800,
        height: int = 600,
        tick_rate_ms: int = 1000 // 60,
        **kwargs,
    ):
        for arg_key in ("width", "height", "tick_rate_ms"):
            arg_val: int = cast(int, locals().get(arg_key))

            if arg_val <= 0:
                raise ValueError(f"nonpositive {arg_key}")

        kwargs.update(width=width, height=height, class_=self.__class__.__name__)
        super().__init__(*args, **kwargs)

        self.__logic_tick = 0
        self.__logic_tick_rate_ms = tick_rate_ms
        self.__reducer = reducer
        self.__state = State(canvas_width=width, canvas_height=height)

        image = _render.Image(width, height)
        self.__renderer = _render.Renderer(image)

        self.__image_label = tkinter.ttk.Label(self, image=image)
        self.__image_label.pack()

        # start runtime loops
        self.after_idle(self.__logic_loop)

    def __logic_loop(self) -> None:
        self.__logic_tick += 1
        self.after(self.__logic_tick_rate_ms, self.__logic_loop)
        new_renderer_state = self.__reducer(self.__logic_tick, copy.copy(self.__state))
        if new_renderer_state and new_renderer_state is not self.__state:
            self.__renderer.render(new_renderer_state)
