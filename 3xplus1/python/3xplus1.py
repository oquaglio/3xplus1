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


# ----------------------------------------------------------------------
# Graceful Ctrl-C
# ----------------------------------------------------------------------
def _sigint_handler(sig, frame):
    print("\nInterrupted by user – exiting.", file=sys.stderr)
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Pure Collatz: no cache, no memoization, no dicts
# ----------------------------------------------------------------------
def collatz_max_height_steps(n: int):
    """Return (max_height, steps) for n. No caching."""
    if n <= 0:
        return 0, 0

    steps = 0
    current = n
    max_height = n

    while current > 1:
        if current > max_height:
            max_height = current

        if current % 2 == 0:
            current //= 2
        else:
            current = 3 * current + 1

        steps += 1

    return max_height, steps


# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def main():
    start = 1
    if len(sys.argv) > 1:
        try:
            start = int(sys.argv[1])
            if start < 1:
                raise ValueError
        except ValueError:
            print("Error: start must be a positive integer", file=sys.stderr)
            sys.exit(1)

    print("number max_height steps cpu_time wall_time")

    cpu_start = time.process_time()
    wall_start = time.monotonic()

    global_max_height = 0
    progress_interval = 1_000_000
    num = start

    while True:
        # Progress indicator
        if num % progress_interval == 0:
            print(f"\r{num}", end="", flush=True)

        # Compute Collatz stats (no cache)
        max_h, steps = collatz_max_height_steps(num)

        # New global maximum?
        if max_h > global_max_height:
            global_max_height = max_h
            cpu_now = time.process_time()
            wall_now = time.monotonic()
            cpu_time = cpu_now - cpu_start
            wall_time = wall_now - wall_start
            print(f"\r{num} {max_h} {steps} {cpu_time:.1f} {wall_time:.0f}")
            sys.stdout.flush()

        # Next number
        num += 1


if __name__ == "__main__":
    main()
