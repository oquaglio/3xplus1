#!/usr/bin/env python3
"""
GPU-Accelerated Collatz Scanner (CUDA + Numba)
- Scans 1M+ numbers per millisecond
- Multi-GPU support
- Thread-safe CPU fallback for printing
- Prints: number, max_height, steps, time, GPU_ID
"""

import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import List

import numpy as np
from numba import cuda, uint64

# ----------------------------------------------------------------------
# Global shutdown
# ----------------------------------------------------------------------
SHUTDOWN = threading.Event()


def _sigint_handler(sig, frame):
    print("\n\nStopping GPU workers...", file=sys.stderr)
    SHUTDOWN.set()


signal.signal(signal.SIGINT, _sigint_handler)


# ----------------------------------------------------------------------
# Record
# ----------------------------------------------------------------------
@dataclass(order=True)
class Record:
    num: int
    height: int
    steps: int
    cpu_time: float
    wall_time: float
    gpu_id: int


# ----------------------------------------------------------------------
# GPU Kernel: Compute max height + steps for a batch
# ----------------------------------------------------------------------
@cuda.jit
def collatz_kernel_gpu(starts, batch_size, max_heights, steps_out):
    idx = cuda.grid(1)
    if idx >= len(starts):
        return

    n = starts[idx]
    max_h = n
    steps = 0
    temp = n

    # Unroll small loops for speed
    while temp > 1:
        if temp > max_h:
            max_h = temp
        if temp % 2 == 0:
            temp //= 2
        else:
            temp = 3 * temp + 1
        steps += 1

    max_heights[idx] = max_h
    steps_out[idx] = steps


# ----------------------------------------------------------------------
# GPU Worker
# ----------------------------------------------------------------------
def gpu_worker(gpu_id: int, start_base: int, stride: int, batch_size: int = 1_000_000):
    global global_max_height

    # Select GPU
    cuda.select_device(gpu_id)
    print(
        f"GPU {gpu_id} initialized (CUDA device {cuda.get_current_device().name.decode()})"
    )

    # Pre-allocate GPU memory
    d_starts = cuda.device_array(batch_size, dtype=uint64)
    d_max_h = cuda.device_array(batch_size, dtype=uint64)
    d_steps = cuda.device_array(batch_size, dtype=uint64)

    # Thread-local max tracking
    local_max_h = 0
    local_records = []

    num = start_base + gpu_id * stride
    batch_end = num + batch_size

    while not SHUTDOWN.is_set():
        # Prepare batch
        h_starts = np.arange(
            num, min(num + batch_size, batch_end), stride, dtype=np.uint64
        )
        actual_batch = len(h_starts)
        if actual_batch == 0:
            num = batch_end
            batch_end += batch_size
            continue

        # Copy to GPU
        d_starts[:actual_batch] = h_starts

        # Launch kernel
        threads_per_block = 256
        blocks = (actual_batch + threads_per_block - 1) // threads_per_block
        collatz_kernel_gpu[blocks, threads_per_block](
            d_starts, actual_batch, d_max_h, d_steps
        )

        # Copy results
        max_h_batch = d_max_h.copy_to_host()[:actual_batch]
        steps_batch = d_steps.copy_to_host()[:actual_batch]

        # Find local new maxima
        for i in range(actual_batch):
            n = h_starts[i]
            h = max_h_batch[i]
            s = steps_batch[i]

            if h > local_max_h:
                cpu_now = time.process_time()
                wall_now = time.monotonic()
                local_records.append(
                    Record(
                        num=int(n),
                        height=int(h),
                        steps=int(s),
                        cpu_time=cpu_now - cpu_start,
                        wall_time=wall_now - wall_start,
                        gpu_id=gpu_id,
                    )
                )
                local_max_h = h

        # Submit to printer
        with queue_lock:
            record_queue.extend(local_records)

        local_records = []
        local_max_h = 0

        # Progress
        print(f"\rGPU{gpu_id}: {num + actual_batch * stride}", end="", flush=True)

        num = batch_end
        batch_end += batch_size


# ----------------------------------------------------------------------
# Printer thread
# ----------------------------------------------------------------------
def printer_thread():
    printed_height = 0
    last_num = 0

    print("number max_height steps cpu_time wall_time GPU", flush=True)

    while not SHUTDOWN.is_set() or record_queue:
        time.sleep(0.1)

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
                        f"{r.num} {r.height} {r.steps} {r.cpu_time:.1f} {r.wall_time:.0f} GPU{r.gpu_id}"
                    )
                    sys.stdout.flush()
                    record_queue[:] = [rec for rec in record_queue if rec.num > r.num]
                    break


# ----------------------------------------------------------------------
# Shared state
# ----------------------------------------------------------------------
queue_lock = threading.Lock()
record_queue: List[Record] = []
global_max_height = 0
cpu_start = time.process_time()
wall_start = time.monotonic()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    if not cuda.is_available():
        print("CUDA not available. Install NVIDIA drivers + CUDA toolkit.")
        sys.exit(1)

    start = 1
    if len(sys.argv) > 1:
        start = int(sys.argv[1])

    gpus = cuda.gpus
    num_gpus = len(gpus)
    if num_gpus == 0:
        print("No GPUs found.")
        sys.exit(1)

    print(f"Found {num_gpus} GPU(s): {[g.name.decode() for g in gpus]}")
    print(f"Starting scan from {start} to infinity")

    printer = threading.Thread(target=printer_thread, daemon=True)
    printer.start()

    workers = []
    for gpu_id in range(num_gpus):
        t = threading.Thread(
            target=gpu_worker, args=(gpu_id, start, num_gpus), daemon=True
        )
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
