#!/usr/bin/env python3
"""
Multi-threaded Collatz scanner – CORRECT ORDER, NO DUPLICATES, MEMORY-SAFE
Uses a queue + printer thread to ensure maxima are printed in order.
"""

import os
import queue
import signal
import sys
import threading
import time
from dataclasses import dataclass

# ----------------------------------------------------------------------
# Global shutdown
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\nInterrupted – stopping all threads...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Result container
# ----------------------------------------------------------------------
@dataclass(order=True)
class Record:
    num: int
    height: int
    steps: int
    cpu_time: float
    wall_time: float


# ----------------------------------------------------------------------
# Pure Collatz
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
# Global state
# ----------------------------------------------------------------------
max_lock = threading.Lock()
global_max_height = 0
result_queue = queue.Queue()  # Thread-safe queue for ordered printing

cpu_start = time.process_time()
wall_start = time.monotonic()


# ----------------------------------------------------------------------
# Printer thread – prints in correct order
# ----------------------------------------------------------------------
def printer_thread():
    printed_max = 0
    while not SHUTDOWN.is_set() or not result_queue.empty():
        try:
            record = result_queue.get(timeout=0.1)
            # Only print if this is the next new max
            if record.height > printed_max:
                printed_max = record.height
                print(
                    f"{record.num} {record.height} {record.steps} {record.cpu_time:.1f} {record.wall_time:.0f}"
                )
                sys.stdout.flush()
            result_queue.task_done()
        except queue.Empty:
            continue


# ----------------------------------------------------------------------
# Worker
# ----------------------------------------------------------------------
def worker(thread_id: int, base: int, stride: int, progress_interval: int = 1_000_000):
    global global_max_height

    num = base + thread_id * stride
    while not SHUTDOWN.is_set():
        if num % progress_interval == 0:
            print(f"\rT{thread_id}: {num}", end="", flush=True)

        max_h, steps = collatz_max_height_steps(num)

        with max_lock:
            if max_h > global_max_height:
                old_max = global_max_height
                global_max_height = max_h
                # Only queue if we actually improved
                if max_h > old_max:
                    cpu_now = time.process_time()
                    wall_now = time.monotonic()
                    record = Record(
                        num=num,
                        height=max_h,
                        steps=steps,
                        cpu_time=cpu_now - cpu_start,
                        wall_time=wall_now - wall_start,
                    )
                    result_queue.put(record)

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
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        SHUTDOWN.set()
        for t in workers:
            t.join()
        printer.join()
        print("\nAll threads stopped.")


if __name__ == "__main__":
    main()
