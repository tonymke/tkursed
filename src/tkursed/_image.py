from typing import ByteString

import PIL.Image

from tkursed import _consts


def rgba_bytes_to_PIL_image(
    data: ByteString, dimensions: tuple[int, int]
) -> PIL.Image.Image:
    """Create a PIL Image from RGBA pixeldata.

    If data is a bytearray, the resulting image is created with a reference
    to it; mutating the bytearray data directly mutates the wrapping PIL Image.

    Arguments:
        data -- ByteString: RGBA pixeldata
        dimensions -- tuple[int, int]: Length and width the represented image.

    Raises:
        ValueError: nonpositive dimensions[0] (width)
        ValueError: nonpositive dimensions[1] (height)
        ValueError: unexpected data len for given dimensions

    Returns:
        PIL.Image.Image: An RGBA PIL Image.
    """

    if dimensions[0] <= 0:
        raise ValueError("nonpositive dimensions[0] (width)")

    if dimensions[1] <= 0:
        raise ValueError("nonpositive dimensions[1] (height)")

    expected_len = dimensions[0] * dimensions[1] * _consts.BITS_PER_PIXEL // 8
    if len(data) != expected_len:
        raise ValueError(
            "unexpected data len for given dimensions",
            ("expected", expected_len),
            ("actual", len(data)),
        )

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
