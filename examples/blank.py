import sys
import tkinter
from tkinter import ttk


class ExampleWindow(tkinter.Tk):
    def __init__(
        self, width=800, height=600, title="A tcl/tkursed 2D renderer", resizable=False
    ):
        super().__init__()
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(resizable, resizable)
        self.frame: ttk.Frame = ttk.Frame(self, width=width, height=height)
        self.frame.pack()


def main() -> int:
    ExampleWindow().mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
