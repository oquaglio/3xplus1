#!/usr/bin/env python3
"""
Infinite Multi-threaded Collatz – CORRECT ORDER + THREAD ID
Prints: number, max_height, steps, cpu_time, wall_time, thread_id
"""

import os
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import List

# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\n\nStopping...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
@dataclass(order=True)
class Record:
    num: int
    height: int
    steps: int
    cpu_time: float
    wall_time: float
    thread_id: int  # NEW: who found it


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
# Shared queue
# ----------------------------------------------------------------------
record_queue: List[Record] = []
queue_lock = threading.Lock()
cpu_start = time.process_time()
wall_start = time.monotonic()


# ----------------------------------------------------------------------
# Worker – collect local maxima with thread_id
# ----------------------------------------------------------------------
def worker(thread_id: int, start_num: int, stride: int, batch_size: int = 100_000):
    num = start_num + thread_id * stride
    local_max_height = 0
    local_records = []

    while not SHUTDOWN.is_set():
        current = num
        batch_end = current + batch_size

        while current < batch_end and not SHUTDOWN.is_set():
            if current % (batch_size // 10) == 0:
                print(f"\rT{thread_id}: {current}", end="", flush=True)

            max_h, steps = collatz_max_height_steps(current)

            if max_h > local_max_height:
                cpu_now = time.process_time()
                wall_now = time.monotonic()
                local_records.append(
                    Record(
                        num=current,
                        height=max_h,
                        steps=steps,
                        cpu_time=cpu_now - cpu_start,
                        wall_time=wall_now - wall_start,
                        thread_id=thread_id,  # Save who found it
                    )
                )
                local_max_height = max_h

            current += stride

        # Submit batch
        with queue_lock:
            record_queue.extend(local_records)

        local_records = []
        local_max_height = 0
        num = batch_end


# ----------------------------------------------------------------------
# Printer – prints in order, with thread_id
# ----------------------------------------------------------------------
def printer_thread():
    printed_height = 0
    last_num = 0

    print("number max_height steps cpu_time wall_time thread", flush=True)

    while not SHUTDOWN.is_set() or record_queue:
        time.sleep(0.5)

        with queue_lock:
            pending = [r for r in record_queue if r.num > last_num]
            if not pending:
                continue
            pending.sort(key=lambda r: r.num)

            for r in pending:
                if r.height > printed_height:
                    printed_height = r.height
                    last_num = r.num
                    print(
                        f"{r.num} {r.height} {r.steps} {r.cpu_time:.1f} {r.wall_time:.0f} T{r.thread_id}"
                    )
                    sys.stdout.flush()
                    record_queue[:] = [rec for rec in record_queue if rec.num > r.num]
                    break


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    start = 1
    if len(sys.argv) > 1:
        start = int(sys.argv[1])
    threads = os.cpu_count() or 4
    if len(sys.argv) > 2:
        threads = int(sys.argv[2])

    print(f"Starting {threads} threads from {start} → ∞")

    printer = threading.Thread(target=printer_thread, daemon=True)
    printer.start()

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


if __name__ == "__main__":
    main()
