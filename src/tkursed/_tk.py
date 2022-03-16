import abc
import sys
import tkinter
import tkinter.messagebox
import tkinter.ttk
import traceback
from typing import cast

from tkursed import _consts, _metrics, _render, _state

AfterKey = str


class Tkursed(tkinter.ttk.Frame):
    """A tkinter widget of a dynamic software-rendered image."""

    __slots__ = (
        "__framerate_monitor",
        "__image_label",
        "__loop_interval_key",
        "__renderer",
        "__run",
        "is_dirty",
        "tick",
        "tkursed_state",
    )

    @property
    def running(self) -> bool:
        """Whether the rendering loop is running and future Tick events
        will be generated."""
        return self.__run

    def __init__(
        self,
        *args,
        width: int = 800,
        height: int = 600,
        tick_rate_ms: int = 1000 // 60,
        **kwargs,
    ):
        """Initialize a new Tkursed widget.

        Keyword Arguments:
            width -- How wide the image should be. (default: {800})
            height -- How tall the image should be (default: {600})
            tick_rate_ms -- How often the image should check for updates to render,
                            in milliseconds. A Tkinter event is raised each tick of this
                            loop. (default: {1000//60})

        Raises:
            ValueError: nonpositive width, height, or tick_rate_ms
        """
        for arg_key in ("width", "height", "tick_rate_ms"):
            arg_val: int = cast(int, locals().get(arg_key))

            if arg_val <= 0:
                raise ValueError(f"nonpositive {arg_key}")

        kwargs.update(width=width, height=height, class_=self.__class__.__name__)
        super().__init__(*args, **kwargs)

        self.__loop_interval_key: AfterKey | None = None
        self.__run = False
        self.is_dirty = False
        self.tick = 0
        self.tkursed_state = _state.State()
        self.tkursed_state.canvas.dimensions = _state.Dimensions(width, height)
        self.tkursed_state.tick_rate_ms = tick_rate_ms

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

        self.__framerate_iter = _metrics.moving_count(1000.0)

        self.bind("<Configure>", self.__handle_frame_configure)
        self.bind("<Destroy>", self.__handle_frame_destroy)
        self.bind("<Map>", self.__handle_frame_map)
        self.bind("<Unmap>", self.__handle_frame_unmap)

    def __handle_frame_configure(self, event: tkinter.Event) -> None:
        self.tkursed_state.canvas.dimensions = _state.Dimensions(
            event.width, event.height
        )
        self.__image_label.place(
            anchor=tkinter.NW,
            width=event.width,
            height=event.height,
        )
        self.is_dirty = True

    def __handle_frame_destroy(self, event: tkinter.Event) -> None:
        self.stop()

    def __handle_frame_map(self, event: tkinter.Event) -> None:
        self.start()

    def __handle_frame_unmap(self, event: tkinter.Event) -> None:
        self.stop()

    def __logic_loop(self, tick: int) -> None:
        if not self.__run:
            self.stop()
            return

        self.tick = tick + 1
        self.__loop_interval_key = self.after(
            self.tkursed_state.tick_rate_ms, self.__logic_loop, tick + 1
        )
        self.event_generate(_consts.EVENT_SEQUENCE_TICK, when="tail")

        if self.is_dirty:
            if validation_errors := self.tkursed_state.validate():
                self.stop()
                self.is_dirty = False
                raise _state.InvalidStateError(validation_errors)

            if new_tk_image := self.__renderer.render(self.tkursed_state):
                self.__image_label.configure(image=new_tk_image)

            self.is_dirty = False

        self.tkursed_state.frame_rate = next(self.__framerate_iter)

    def start(self) -> None:
        """Idempotently start the rendering loop."""
        self.__run = True
        if not self.__loop_interval_key:
            self.__loop_interval_key = self.after_idle(self.__logic_loop, self.tick)

    def stop(self) -> None:
        """Idempotently stop the rendering loop."""
        self.__run = False
        if key := self.__loop_interval_key:
            self.__loop_interval_key = None
            self.after_cancel(key)


class SimpleTkursedWindow(tkinter.Tk, metaclass=abc.ABCMeta):
    """A simple abstract Tkinter window for the most basic use cases.

    Note that only onetinter.Tk can ever exist per thread."""

    def __init__(
        self,
        title: str = "A tcl/tkursed 2D renderer",
        width: int = 800,
        height: int = 600,
        tick_rate_ms: int = 1000 // 60,
        *args,
        **kwargs,
    ) -> None:
        super().__init__()
        self.title(title)

        self.minsize(320, 200)
        self.maxsize(1024, 768)

        self.tkursed = Tkursed(
            self, *args, width=width, height=height, tick_rate_ms=tick_rate_ms, **kwargs
        )
        self.tkursed.pack(
            fill=tkinter.BOTH,
            expand=True,
            anchor=tkinter.CENTER,
        )
        self.bind(_consts.EVENT_SEQUENCE_TICK, self.handle_tick)

    def report_callback_exception(self, exc, val, tb):
        """tkinter callback invoked when an unhandled exception is risen by
        a callback in its event loop."""
        printed = False
        self.tkursed.stop()
        try:
            traceback.print_exception(exc, val, tb, file=sys.stderr)
            printed = True
        except IOError:
            # Pipe is closed. Nothing we can do.
            pass
        else:
            msg = (
                f"An unhandled {exc.__name__} has occurred and Tkursed's"
                " rendering loop has stopped."
            )
            if printed:
                msg += "\n\nSee stderr for debugging information."

            tkinter.messagebox.showerror("Unhandled exception", msg)

    @abc.abstractmethod
    def handle_tick(self, event: tkinter.Event) -> None:
        """Your application's rendering tick handler.

        Update the image to be drawn by mutating self.tkursed.tkursed_state,
        and indicating updates were made by setting self.tkursed.is_dirty=True before
        returning.
        """
        raise NotImplementedError
