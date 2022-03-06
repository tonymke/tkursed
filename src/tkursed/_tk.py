import tkinter
import tkinter.ttk
from typing import cast

from tkursed import _consts, _render
from tkursed._state import Dimensions, State

AfterKey = str


class Tkursed(tkinter.ttk.Frame):
    __slots__ = (
        "__image_label",
        "__loop_interval_key",
        "__renderer",
        "__run",
        "is_dirty",
        "tick",
        "tkursed_state",
    )

    def __init__(
        self,
        *args,
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

        self.__run = False
        self.__loop_interval_key: AfterKey | None = None
        self.tick = 0
        self.is_dirty = False
        self.tkursed_state = State()
        self.tkursed_state.tick_rate_ms = tick_rate_ms
        self.tkursed_state.canvas.dimensions = Dimensions(width, height)

        self.__renderer = _render.Renderer()

        tk_image = self.__renderer.render(self.tkursed_state)
        if not tk_image:
            raise RuntimeError("first render did not return tk image ref")

        self.__image_label = tkinter.ttk.Label(self, image=tk_image)
        self.__image_label.place(
            anchor=tkinter.NW,
            width=width,
            height=height,
        )

        self.bind("<Configure>", self.__handle_frame_configure)
        self.bind("<Destroy>", self.__handle_frame_destroy)
        self.bind("<Map>", self.__handle_frame_map)
        self.bind("<Unmap>", self.__handle_frame_unmap)

    def __handle_frame_configure(self, event: tkinter.Event) -> None:
        self.tkursed_state.canvas.dimensions = Dimensions(event.width, event.height)
        self.__image_label.place(
            anchor=tkinter.NW,
            width=event.width,
            height=event.height,
        )
        self.is_dirty = True

    def __handle_frame_map(self, event: tkinter.Event) -> None:
        self.__run = True
        if not self.__loop_interval_key:
            self.__loop_interval_key = self.after_idle(self.__logic_loop, self.tick)

    def __handle_frame_destroy(self, event: tkinter.Event) -> None:
        self.__run = False
        if key := self.__loop_interval_key:
            self.__loop_interval_key = None
            self.after_cancel(key)

    __handle_frame_unmap = __handle_frame_destroy

    def __logic_loop(self, tick: int) -> None:
        if not self.__run:
            self.__loop_interval_key = None
            return

        self.tick = tick + 1
        self.__loop_interval_key = self.after(
            self.tkursed_state.tick_rate_ms, self.__logic_loop, tick + 1
        )
        self.event_generate(_consts.EVENT_SEQUENCE_TICK, when="now")

        if self.is_dirty:
            if new_tk_image := self.__renderer.render(self.tkursed_state):
                self.__image_label.configure(image=new_tk_image)
            self.is_dirty = False
