"""Tools for recording runtime metrics."""

import collections
import time
from collections.abc import Generator


def moving_count(
    window_duration_ms: int | float = 1000.0,
) -> Generator[int, None, None]:
    """Generate a moving-window count based on the amount of next() calls.

    Keyword Arguments:
        window_duration_ms -- int | float: the size of the moving window, in
                              milliseconds (default: {1000.0})

    Raises:
        ValueError: nonpositive window_duration_ms

    Yields:
        The amount of next() calls made in the last window_duration_ms milliseconds as
        of the time of the invoking next() call.
    """
    if window_duration_ms <= 0:
        raise ValueError("nonpositive window_duration_ms")

    window_duration_s = window_duration_ms / 1000.0
    q: collections.deque[float] = collections.deque()

    while True:
        now = time.time()
        q.append(now)
        cutoff = now - window_duration_s
        while q and q[0] < cutoff:
            q.popleft()

        yield len(q)
