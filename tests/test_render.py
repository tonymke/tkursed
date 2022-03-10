import tkursed


def test_background_render() -> None:
    unit = tkursed.Renderer()
    unit.render(
        tkursed.State(
            canvas=tkursed.Canvas(
                background_color=(1, 2, 3), dimensions=tkursed.Dimensions(10, 10)
            )
        ),
        __is_headless=True,
    )
    assert bytes(unit) == bytes((1, 2, 3, 255) * 10 * 10)
