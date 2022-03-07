import sys
import tkinter

import PIL.Image

import tkursed


class SquareExample(tkursed.SimpleTkursedWindow):
    def handle_tick(self, event: tkinter.Event) -> None:
        if self.tkursed.tick == 16:
            self.tkursed.tkursed_state.canvas.sprites = [
                tkursed.PositionedSprite(
                    tkursed.Coordinates(50, 50),
                    tkursed.Image(PIL.Image.new("RGBA", (100, 100), color="#FF0000")),
                )
            ]
            self.tkursed.is_dirty = True


def main() -> int:
    SquareExample().mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Caught SIGINT", file=sys.stderr)
        sys.exit(1)
