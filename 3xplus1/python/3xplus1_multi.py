#!/usr/bin/env python3
"""
Infinite Multi-threaded Collatz Scanner
- No upper limit
- Correct order
- No cache, no OOM
- Ctrl+C to stop
"""

import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import List

# ----------------------------------------------------------------------
# Global shutdown
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\n\nStopping all threads... (this may take a moment)", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Record for new maxima
# ----------------------------------------------------------------------
@dataclass
class Record:
    num: int
    height: int
    steps: int
    cpu_time: float
    wall_time: float

    def __lt__(self, other):
        return self.num < other.num


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
# Shared state
# ----------------------------------------------------------------------
max_lock = threading.Lock()
global_max_height = 0
records: List[Record] = []

cpu_start = time.process_time()
wall_start = time.monotonic()


# ----------------------------------------------------------------------
# Worker thread
# ----------------------------------------------------------------------
def worker(thread_id: int, start_num: int, stride: int, batch_size: int = 1_000_000):
    global global_max_height

    num = start_num + thread_id * stride
    batch_end = num + batch_size

    while not SHUTDOWN.is_set():
        local_records = []

        # Process one batch
        current = num
        while current < batch_end and not SHUTDOWN.is_set():
            if current % (batch_size // 10) == 0:
                print(f"\rT{thread_id}: {current}", end="", flush=True)

            max_h, steps = collatz_max_height_steps(current)

            with max_lock:
                if max_h > global_max_height:
                    global_max_height = max_h
                    cpu_now = time.process_time()
                    wall_now = time.monotonic()
                    local_records.append(
                        Record(
                            num=current,
                            height=max_h,
                            steps=steps,
                            cpu_time=cpu_now - cpu_start,
                            wall_time=wall_now - wall_start,
                        )
                    )

            current += stride

        # Append local records atomically
        with max_lock:
            records.extend(local_records)

        # Next batch
        num = batch_end
        batch_end += batch_size


# ----------------------------------------------------------------------
# Printer thread – prints in order, only when height increases
# ----------------------------------------------------------------------
def printer_thread():
    printed_height = 0
    last_printed_num = 0

    while not SHUTDOWN.is_set() or records:
        time.sleep(0.5)  # check every 500ms

        with max_lock:
            # Get all records up to current max
            pending = [r for r in records if r.num > last_printed_num]
            if not pending:
                continue
            pending.sort(key=lambda r: r.num)

            # Print only new height increases
            for r in pending:
                if r.height > printed_height:
                    printed_height = r.height
                    last_printed_num = r.num
                    print(
                        f"\n{r.num} {r.height} {r.steps} {r.cpu_time:.1f} {r.wall_time:.0f}"
                    )
                    sys.stdout.flush()
                    records[:] = [
                        rec for rec in records if rec.num > r.num
                    ]  # keep future
                    break


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
            print("Error: start must be positive integer", file=sys.stderr)
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

    print(f"Starting {threads} threads from {start} → ∞")
    print("number max_height steps cpu_time wall_time")
    sys.stdout.flush()

    # Start printer
    printer = threading.Thread(target=printer_thread, daemon=True)
    printer.start()

    # Start workers
    workers = []
    for tid in range(threads):
        t = threading.Thread(target=worker, args=(tid, start, threads), daemon=True)
        t.start()
        workers.append(t)

    try:
        while not SHUTDOWN.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        SHUTDOWN.set()
        for t in workers:
            t.join()
        printer.join()
        print("\n\nStopped. Final max height:", global_max_height)


if __name__ == "__main__":
    main()
