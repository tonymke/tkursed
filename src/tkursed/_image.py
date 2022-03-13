from typing import ByteString

import PIL.Image


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
        ValueError: width (dimensions[0]) is <=0
        ValueError: height (dimensions[1]) is <=0

    Returns:
        PIL.Image.Image: An RGBA PIL Image.
    """

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
