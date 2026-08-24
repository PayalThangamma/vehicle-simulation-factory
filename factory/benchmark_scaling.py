import argparse
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

PYTHON = (
    Path.home()
    / "AppData"
    / "Local"
    / "Programs"
    / "Python"
    / "Python312"
    / "python.exe"
)

RUN_FACTORY = (
    ROOT
    / "factory"
    / "run_factory.py"
)


def run_benchmark(
    workers,
    model_version,
    duration,
):
    command = [
        str(PYTHON),
        str(RUN_FACTORY),
        "--workers",
        str(workers),
        "--model-version",
        model_version,
        "--duration",
        str(duration),
    ]

    start_time = time.perf_counter()

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    wall_time = (
        time.perf_counter()
        -
        start_time
    )

    if process.returncode != 0:
        raise RuntimeError(
            process.stderr
        )

    throughput = None

    for line in process.stdout.splitlines():
        if line.strip().startswith(
            "Throughput:"
        ):
            value = (
                line.split(
                    ":",
                    1,
                )[1]
                .strip()
                .split()[0]
            )

            throughput = float(
                value
            )

    if throughput is None:
        raise RuntimeError(
            "Could not parse throughput."
        )

    return {
        "workers": workers,
        "wall_time": wall_time,
        "throughput": throughput,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-version",
        default="v3",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
    )

    parser.add_argument(
        "--workers",
        nargs="+",
        type=int,
        default=[
            1,
            2,
            4,
            8,
        ],
    )

    args = parser.parse_args()

    results = []

    print()
    print(
        "============================================"
    )
    print(
        "Parallel Scaling Benchmark"
    )
    print(
        "============================================"
    )

    for worker_count in args.workers:
        print()
        print(
            f"Running with {worker_count} worker(s)..."
        )

        result = run_benchmark(
            worker_count,
            args.model_version,
            args.duration,
        )

        results.append(
            result
        )

        print(
            f"Wall time:   {result['wall_time']:.3f} s"
        )

        print(
            f"Throughput:  {result['throughput']:.2f} simulations/s"
        )

    baseline_time = results[
        0
    ][
        "wall_time"
    ]

    print()
    print(
        "============================================"
    )
    print(
        "Scaling Summary"
    )
    print(
        "============================================"
    )

    print(
        f"{'Workers':<10}"
        f"{'Wall Time':<15}"
        f"{'Throughput':<18}"
        f"{'Speedup':<12}"
        f"{'Efficiency':<12}"
    )

    print(
        "-" * 67
    )

    for result in results:
        workers = result[
            "workers"
        ]

        wall_time = result[
            "wall_time"
        ]

        throughput = result[
            "throughput"
        ]

        speedup = (
            baseline_time
            /
            wall_time
        )

        efficiency = (
            speedup
            /
            workers
            *
            100.0
        )

        print(
            f"{workers:<10}"
            f"{wall_time:<15.3f}"
            f"{throughput:<18.2f}"
            f"{speedup:<12.2f}"
            f"{efficiency:<12.2f}%"
        )

    print(
        "============================================"
    )


if __name__ == "__main__":
    main()