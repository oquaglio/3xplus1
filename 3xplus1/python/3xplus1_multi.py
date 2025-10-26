#!/usr/bin/env pypy3
"""
Unlimited-size, multi-threaded Collatz (3x+1) conjecture scanner.
PyPy strongly recommended for maximum speed.

Usage:
    pypy3 collatz_mt.py [start] [threads]

    start     – first number to test (default: 1)
    threads   – number of worker threads (default: CPU cores)
"""

import os
import signal
import sys
import threading
import time
from typing import Dict, Tuple

# ----------------------------------------------------------------------
# Graceful Ctrl-C shutdown
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\nInterrupted – stopping all threads...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Thread-local cache (one per thread → no contention)
# ----------------------------------------------------------------------
class LocalCache:
    __slots__ = ("data",)

    def __init__(self) -> None:
        self.data: Dict[int, Tuple[int, int]] = {}


def collatz_max_height_steps(n: int, cache: LocalCache) -> Tuple[int, int]:
    """Return (max_height, steps) for Collatz sequence starting at n."""
    if n <= 0:
        return 0, 0
    if n in cache.data:
        return cache.data[n]

    steps = 0
    cur = n
    max_h = n

    while cur > 1:
        if cur > max_h:
            max_h = cur

        if cur % 2 == 0:
            cur //= 2
        else:
            cur = 3 * cur + 1

        steps += 1

        # Use cached tail if available
        if cur in cache.data:
            cached_h, cached_s = cache.data[cur]
            max_h = max(max_h, cached_h)
            steps += cached_s
            break

    cache.data[n] = (max_h, steps)
    return max_h, steps


# ----------------------------------------------------------------------
# Global state for new maximum reporting
# ----------------------------------------------------------------------
global_max_lock = threading.Lock()
global_max_height: int = 0

cpu_start = time.process_time()
wall_start = time.monotonic()


def report_new_max(num: int, max_h: int, steps: int) -> None:
    """Thread-safe: print when a new global max height is found."""
    global global_max_height
    with global_max_lock:
        if max_h > global_max_height:
            global_max_height = max_h
            cpu_now = time.process_time()
            wall_now = time.monotonic()
            cpu_time = cpu_now - cpu_start
            wall_time = wall_now - wall_start
            print(f"\r{num} {max_h} {steps} {cpu_time:.1f} {wall_time:.0f}")
            sys.stdout.flush()


# ----------------------------------------------------------------------
# Worker thread
# ----------------------------------------------------------------------
def worker(
    thread_id: int, base: int, stride: int, progress_interval: int = 1_000_000
) -> None:
    cache = LocalCache()
    num = base + thread_id * stride

    while not SHUTDOWN.is_set():
        # Progress indicator
        if num % progress_interval == 0:
            print(f"\rT{thread_id}: {num}", end="", flush=True)

        max_h, steps = collatz_max_height_steps(num, cache)

        if max_h > global_max_height:
            report_new_max(num, max_h, steps)

        num += stride


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> None:
    start = 1
    if len(sys.argv) > 1:
        try:
            start = int(sys.argv[1])
            if start < 1:
                raise ValueError
        except ValueError:
            print("Error: start must be a positive integer", file=sys.stderr)
            sys.exit(1)

    # Use os.cpu_count(), not threading.cpu_count()
    threads = os.cpu_count() or 4
    if len(sys.argv) > 2:
        try:
            threads = int(sys.argv[2])
            if threads < 1:
                raise ValueError
        except ValueError:
            print("Error: thread count must be a positive integer", file=sys.stderr)
            sys.exit(1)

    print(f"Starting {threads} threads, base = {start}")
    print("number max_height steps cpu_time wall_time")

    workers = []
    for tid in range(threads):
        t = threading.Thread(target=worker, args=(tid, start, threads), daemon=True)
        t.start()
        workers.append(t)

    # Keep main thread alive
    try:
        while not SHUTDOWN.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        SHUTDOWN.set()
        for t in workers:
            t.join()
        print("\nAll threads stopped.")


if __name__ == "__main__":
    main()
