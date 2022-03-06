from typing import ByteString

import PIL.Image


def rgba_bytes_to_PIL_image(
    data: ByteString, dimensions: tuple[int, int]
) -> PIL.Image.Image:

    if dimensions[0] <= 0:
        raise ValueError("nonpositive width")

    if dimensions[1] <= 0:
        raise ValueError("nonpositive height")

    if isinstance(data, bytearray):
        fn = PIL.Image.frombuffer
    else:
        fn = PIL.Image.frombytes

    return fn(
        "RGBA",  # mode
        dimensions,  # size tuple
        data,  # data buffer
        "raw",  # decoder name
        "RGBA",  # decoder arg - mode
        0,  # decoder arg - stride (bits between pixels)
        1,  # decoder arg - orientation - up
    )
