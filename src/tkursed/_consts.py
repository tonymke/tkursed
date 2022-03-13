from typing import Final as _Final

BPP: _Final[int] = 32
"""The amount of bits per pixel in a RGBA pixeldata."""

BITS_PER_PIXEL: _Final[int] = BPP
"""The amount of bits per pixel in a RGBA pixeldata."""

EVENT_SEQUENCE_TICK = "<<tkursedtick>>"
"""Tkinter Event Sequence of Tkursed's rendering loop.

An event is emitted with this sequence for each tick of the the Tkursed rendering
loop and can be relied upon for syncing with it.
"""
