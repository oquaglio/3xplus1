#!/usr/bin/env python3
"""
Unlimited-size Collatz conjecture scanner – Python version of the C program.

Features
--------
* start value from command line (default = 1)
* no upper bound on the numbers (Python int = arbitrary precision)
* prints a line every time a new global maximum height is discovered:
      number max_height steps cpu_time wall_time
* progress indicator every 1 000 000 numbers
* Ctrl-C aborts cleanly
* optional simple cache (memoisation) for already-seen values

Usage
-----
# Start from 1 (will run forever, printing new maxima)
python3 collatz_unlimited.py

# Start from a higher number
python3 collatz_unlimited.py 1000000

Exmples
-------
$ python3 3xplus1.py [start]
$ python3 3xplus1.py 1000000
$ python3 3xplus1.py 12345678901234567890
$ python3 3xplus1.py 100
"""

import signal
import sys
import time
from typing import Dict, Tuple


# ----------------------------------------------------------------------
# Graceful Ctrl-C
# ----------------------------------------------------------------------
def _sigint_handler(sig, frame):
    print("\nInterrupted by user – exiting.")
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)

# ----------------------------------------------------------------------
# Optional cache – speeds up repeated sub-sequences
# ----------------------------------------------------------------------
CACHE: Dict[int, Tuple[int, int]] = {}  # key → (max_height, steps)


def collatz_max_height_steps(n: int) -> Tuple[int, int]:
    """Return (max_height, steps) for the Collatz sequence starting at n."""
    if n <= 0:
        return 0, 0
    if n in CACHE:
        return CACHE[n]

    steps = 0
    cur = n
    max_h = n

    while cur > 1:
        if cur > max_h:
            max_h = cur

        if cur % 2 == 0:
            cur //= 2
        else:
            cur = 3 * cur + 1  # no overflow possible with Python int

        steps += 1

        # If we have already computed this intermediate value, splice in the
        # cached result and finish early.
        if cur in CACHE:
            cached_h, cached_s = CACHE[cur]
            max_h = max(max_h, cached_h)
            steps += cached_s
            break

    # Store the result for the original n (not for intermediates that were
    # spliced in – they are stored when they are first encountered).
    CACHE[n] = (max_h, steps)
    return max_h, steps


# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def main() -> None:
    start = 1

    if len(sys.argv) > 1:
        try:
            start = int(sys.argv[1])
            if start < 1:
                raise ValueError
        except ValueError:
            print("Error: start value must be a positive integer", file=sys.stderr)
            sys.exit(1)

    print("number max_height steps cpu_time wall_time")

    cpu_start = time.process_time()
    wall_start = time.monotonic()

    global_max = 0
    progress_interval = 1_000_000
    num = start

    while True:  # infinite loop – break only on overflow or user abort
        # ----- progress -------------------------------------------------
        if num % progress_interval == 0:
            print(f"\r{num}", end="", flush=True)

        # ----- compute --------------------------------------------------
        max_h, steps = collatz_max_height_steps(num)

        # ----- new global maximum ---------------------------------------
        if max_h > global_max:
            global_max = max_h
            cpu_now = time.process_time()
            wall_now = time.monotonic()

            cpu_time = cpu_now - cpu_start
            wall_time = wall_now - wall_start

            print(f"\r{num} {max_h} {steps} {cpu_time:.1f} {wall_time:.0f}")
            sys.stdout.flush()

        # ----- advance --------------------------------------------------
        num += 1
        # (no upper-bound check – Python int can represent any size)

    # never reached


if __name__ == "__main__":
    main()
