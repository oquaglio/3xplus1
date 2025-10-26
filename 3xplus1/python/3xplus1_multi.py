#!/usr/bin/env python3
"""
Multi-threaded Collatz scanner – NO CACHE, MEMORY-SAFE, RACE-FREE
Prints a line **only** when a NEW GLOBAL MAXIMUM height is found.
Output is identical to the single-threaded version.
"""

import os
import signal
import sys
import threading
import time

# ----------------------------------------------------------------------
# Global shutdown
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\nInterrupted – stopping all threads...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Pure Collatz – no cache
# ----------------------------------------------------------------------
def collatz_max_height_steps(n: int):
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
# Global state – protected by max_lock
# ----------------------------------------------------------------------
max_lock = threading.Lock()

global_max_height = 0  # current best height
record_num = 0  # number that gave it
record_steps = 0  # steps for that number

cpu_start = time.process_time()
wall_start = time.monotonic()


# ----------------------------------------------------------------------
# Worker – atomic update + print only if we raised the max
# ----------------------------------------------------------------------
def worker(thread_id: int, base: int, stride: int, progress_interval: int = 1_000_000):
    # Declare globals we will modify – MUST BE FIRST
    global global_max_height, record_num, record_steps

    num = base + thread_id * stride
    while not SHUTDOWN.is_set():
        # ---- progress -------------------------------------------------
        if num % progress_interval == 0:
            print(f"\rT{thread_id}: {num}", end="", flush=True)

        # ---- compute --------------------------------------------------
        max_h, steps = collatz_max_height_steps(num)

        # ---- ATOMIC update + decide if we print -----------------------
        print_it = False
        with max_lock:
            if max_h > global_max_height:
                global_max_height = max_h
                record_num = num
                record_steps = steps
                print_it = True  # only the winner sets this

        # ---- print outside lock (fast) --------------------------------
        if print_it:
            cpu_now = time.process_time()
            wall_now = time.monotonic()
            cpu_time = cpu_now - cpu_start
            wall_time = wall_now - wall_start
            print(
                f"\r{record_num} {max_h} {record_steps} {cpu_time:.1f} {wall_time:.0f}"
            )
            sys.stdout.flush()

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
