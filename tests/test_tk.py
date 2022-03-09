import tkinter
from typing import Callable, Final, Generator

import _tkinter
import pytest

import tkursed

EVENT_SEQUENCE_DESTROY: Final[str] = "<Destroy>"
unit_test_tick_handler_t = Callable[[tkinter.Toplevel, tkursed.Tkursed], None]
unit_test_ex_handler_t = Callable[[Exception], None]


@pytest.fixture(scope="module")
def simple_tick_handler_factory():
    def factory(stop_at_tick: int):
        def impl(
            window: tkinter.Tk, unit: tkursed.Tkursed, event: tkinter.Event
        ) -> bool:
            nonlocal stop_at_tick
            return unit.tick >= stop_at_tick

        return impl

    return factory


class UnitTestRoot(tkinter.Tk):
    def __init__(self):
        super().__init__()

        self.ut_window: tkinter.Toplevel | None = None
        self.ut_window_bind: str | None = None
        self.withdraw()

    def new_window(self, ut_window: tkinter.Toplevel):
        self.cleanup_current_window()
        self.ut_window = ut_window
        self.ut_window.bind(EVENT_SEQUENCE_DESTROY, self.handle_window_destroy)

    def handle_window_destroy(self, event: tkinter.Event) -> None:
        self.cleanup_current_window()

    def cleanup_current_window(self) -> None:
        if self.ut_window_bind:
            try:
                self.unbind(EVENT_SEQUENCE_DESTROY, self.ut_window_bind)
            except Exception:
                pass

        if self.ut_window:
            try:
                self.ut_window.destroy()
            except Exception:
                pass

        self.ut_window_bind = None
        self.ut_window = None


# There can only ever be one Tk root per python process.
@pytest.fixture(scope="session")
def ut_root():
    root = UnitTestRoot()
    yield root

    root.cleanup_current_window()

    try:
        root.destroy()
    except Exception:
        pass


class UnitTestWindow(tkinter.Toplevel):
    def __init__(
        self,
        parent: tkinter.Misc,
        unit_test_tick_handler: unit_test_tick_handler_t,
        unit_test_ex_handler: unit_test_ex_handler_t,
        title: str = "A tcl/tkursed 2D renderer",
        width: int = 60,
        height: int = 60,
        tick_rate_ms: int = 1000 // 30,
    ) -> None:
        super().__init__(parent)
        self.title(title)

        self.tkursed = tkursed.Tkursed(
            self,
            width=width,
            height=height,
            tick_rate_ms=tick_rate_ms,
        )
        self.tkursed.pack(
            fill=tkinter.BOTH,
            expand=True,
            anchor=tkinter.CENTER,
        )
        self.unit_test_tick_handler = unit_test_tick_handler
        self.unit_test_ex_handler = unit_test_ex_handler
        self.child_destroyed = False
        self.bind(tkursed.EVENT_SEQUENCE_TICK, self.handle_tick)
        self.tkursed.bind("<Destroy>", self.__handle_destroy_child)
        self.withdraw()

    def handle_tick(self, event: tkinter.Event) -> None:
        try:
            self.unit_test_tick_handler(self, self.tkursed)
        except Exception as ex:
            self.unit_test_ex_handler(ex)
            self.tkursed.stop()
            self.update_idletasks()
            self.destroy()

    def __handle_destroy_child(self, event: tkinter.Event) -> None:
        self.child_destroyed = True
        self.destroy()

    def report_callback_exception(self, exc, val, tb):
        self.tkursed.stop()
        self.destroy()


@pytest.fixture
def ut_window_factory(
    ut_root,
) -> Generator[
    Callable[[unit_test_tick_handler_t, unit_test_ex_handler_t], UnitTestWindow],
    None,
    None,
]:
    ut_window: UnitTestWindow | None = None

    def factory(
        tick_handler: unit_test_tick_handler_t, ex_handler: unit_test_ex_handler_t
    ) -> UnitTestWindow:
        nonlocal ut_window, ut_root
        ut_window = UnitTestWindow(
            ut_root,
            unit_test_tick_handler=tick_handler,
            unit_test_ex_handler=ex_handler,
        )
        return ut_window

    yield factory
    ut_root.cleanup_current_window()


def run_tkinter_test_fn(
    ut_root: UnitTestRoot,
    ut_window_factory: Callable[
        [unit_test_tick_handler_t, unit_test_ex_handler_t], UnitTestWindow
    ],
    tick_handler: unit_test_tick_handler_t,
) -> tuple[tkursed.State, list[Exception]]:
    run = True
    started = False
    exceptions = []

    def ex_handler(ex: Exception):
        nonlocal exceptions, run
        exceptions.append(ex)
        run = False

    ut_window = ut_window_factory(tick_handler, ex_handler)

    unit_state = ut_window.tkursed.tkursed_state

    ut_window.tkursed.start()

    while (
        run
        and not ut_window.child_destroyed
        and (ut_window.tkursed.running or not started)
    ):
        if not started:
            ut_window.tkursed.start()
            started = True
        ut_root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT)

    return unit_state, exceptions


def test_tick_increment(
    ut_root: UnitTestRoot,
    ut_window_factory: Callable[
        [unit_test_tick_handler_t, unit_test_ex_handler_t], UnitTestWindow
    ],
):
    tick = 0

    def tick_handler(window: tkinter.Toplevel, unit: tkursed.Tkursed):
        nonlocal tick
        tick = unit.tick
        if unit.tick >= 3:
            unit.stop()

    _, exceptions = run_tkinter_test_fn(
        ut_root=ut_root, ut_window_factory=ut_window_factory, tick_handler=tick_handler
    )
    assert len(exceptions) == 0
    assert tick == 3
