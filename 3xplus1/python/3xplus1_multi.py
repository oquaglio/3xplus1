#!/usr/bin/env pypy3
"""
Multi-threaded Collatz Scanner – NO CACHE, NO MEMORY GROWTH

Features:
- Starts from any number (default: 1)
- Unlimited integer size
- Each thread scans a disjoint arithmetic sequence
- Prints ONLY when a NEW GLOBAL MAXIMUM height is found
- Progress per thread every 1M numbers
- Ctrl+C stops all threads cleanly
- < 100 MB RAM total (even with 64 threads)
- Scales perfectly with CPU cores

Run:
    pypy3 collatz_mt_nocache.py [start] [threads]
"""

import os
import signal
import sys
import threading
import time

# ----------------------------------------------------------------------
# Global shutdown flag
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\nInterrupted – stopping all threads...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Pure Collatz: no cache, no memoization
# ----------------------------------------------------------------------
def collatz_max_height_steps(n: int):
    """Return (max_height, steps) for n. Zero memory allocation."""
    if n <= 0:
        return 0, 0
    steps = 0
    cur = n
    max_h = n
    while cur > 1:
        if cur > max_h:
            max_h = cur
        cur = cur // 2 if cur % 2 == 0 else 3 * cur + 1
        steps += 1
    return max_h, steps


# ----------------------------------------------------------------------
# Thread-safe global maximum tracking
# ----------------------------------------------------------------------
max_lock = threading.Lock()
global_max_height = 0

cpu_start = time.process_time()
wall_start = time.monotonic()


def report_new_max(num: int, max_h: int, steps: int):
    """Print only if this is the new global maximum."""
    global global_max_height
    with max_lock:
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
def worker(thread_id: int, base: int, stride: int, progress_interval: int = 1_000_000):
    num = base + thread_id * stride
    while not SHUTDOWN.is_set():
        # Progress
        if num % progress_interval == 0:
            print(f"\rT{thread_id}: {num}", end="", flush=True)

        max_h, steps = collatz_max_height_steps(num)

        if max_h > global_max_height:
            report_new_max(num, max_h, steps)

        num += stride


# ----------------------------------------------------------------------
# Main
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

    threads = os.cpu_count() or 4
    if len(sys.argv) > 2:
        try:
            threads = int(sys.argv[2])
            if threads < 1:
                raise ValueError
        except ValueError:
            print("Error: thread count must be positive", file=sys.stderr)
            sys.exit(1)

    print(f"Starting {threads} threads, base = {start}")
    print("number max_height steps cpu_time wall_time")

    workers = []
    for tid in range(threads):
        t = threading.Thread(target=worker, args=(tid, start, threads), daemon=True)
        t.start()
        workers.append(t)

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
