import copy
import tkinter
import tkinter.ttk
from typing import cast

from tkursed import _render
from tkursed._state import Dimensions, Reducer, State


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
        self.__state = State(canvas_dimensions=Dimensions(width, height))

        self.__renderer = _render.Renderer()

        tk_image = self.__renderer.render(self.__state)
        if not tk_image:
            raise RuntimeError("first render did not return tk image ref")

        self.__image_label = tkinter.ttk.Label(self, image=tk_image)
        self.__image_label.pack()

        self.after_idle(self.__logic_loop)

    def __logic_loop(self) -> None:
        self.__logic_tick += 1
        self.after(self.__logic_tick_rate_ms, self.__logic_loop)
        new_renderer_state = self.__reducer(self.__logic_tick, copy.copy(self.__state))
        if new_renderer_state and new_renderer_state is not self.__state:
            self.__renderer.render(new_renderer_state)
