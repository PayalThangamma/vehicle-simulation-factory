import argparse
import csv
import json
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)

RUN_FACTORY = (
    ROOT
    / "factory"
    / "run_factory.py"
)

PYTHON = (
    Path.home()
    / "AppData"
    / "Local"
    / "Programs"
    / "Python"
    / "Python312"
    / "python.exe"
)

REPORT_DIR = (
    ROOT
    / "results"
    / "reports"
)

CSV_PATH = (
    REPORT_DIR
    / "scaling_benchmark.csv"
)


def create_benchmark_dataset(
    count,
    output_directory,
):
    source_paths = sorted(
        SOURCE_SCENARIO_DIR.glob(
            "*.json"
        )
    )

    if not source_paths:
        raise RuntimeError(
            "No source scenarios found."
        )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    for index in range(count):
        source_path = source_paths[
            index
            %
            len(source_paths)
        ]

        with open(
            source_path,
            "r",
            encoding="utf-8",
        ) as file:
            scenario = json.load(
                file
            )

        scenario[
            "scenario_id"
        ] = (
            f"bench_{count:05d}_{index + 1:05d}"
        )

        output_path = (
            output_directory
            /
            f"{scenario['scenario_id']}.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                scenario,
                file,
                indent=2,
            )


def run_factory(
    scenario_directory,
    count,
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
        "--scenario-dir",
        str(scenario_directory),
        "--no-db",
        "--quiet",
    ]

    process_start = time.perf_counter()

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    process_wall_time = (
        time.perf_counter()
        -
        process_start
    )

    if process.returncode != 0:
        print(
            process.stdout
        )

        print(
            process.stderr
        )

        raise RuntimeError(
            f"Benchmark failed for {count} scenarios "
            f"with {workers} workers."
        )

    summary = None

    for line in process.stdout.splitlines():
        if line.startswith(
            "FACTORY_SUMMARY="
        ):
            summary = json.loads(
                line.split(
                    "=",
                    1,
                )[1]
            )

            break

    if summary is None:
        raise RuntimeError(
            "Could not find factory summary."
        )

    summary[
        "process_wall_time_s"
    ] = process_wall_time

    summary[
        "process_throughput"
    ] = (
        count
        /
        process_wall_time
        if process_wall_time > 0.0
        else 0.0
    )

    return summary


def save_csv(results):
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "scenario_count",
        "workers",
        "duration",
        "preparation_time_s",
        "execution_time_s",
        "processing_time_s",
        "internal_total_time_s",
        "process_wall_time_s",
        "execution_throughput",
        "total_throughput",
        "process_throughput",
        "speedup",
        "efficiency_percent",
    ]

    with open(
        CSV_PATH,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(
                {
                    field: result.get(field)
                    for field in fields
                }
            )


def calculate_scaling(results):
    grouped = {}

    for result in results:
        count = result[
            "scenario_count"
        ]

        grouped.setdefault(
            count,
            [],
        ).append(
            result
        )

    for count, group in grouped.items():
        group.sort(
            key=lambda item: item[
                "workers"
            ]
        )

        baseline = next(
            (
                item
                for item in group
                if item[
                    "workers"
                ] == 1
            ),
            None,
        )

        if baseline is None:
            continue

        baseline_time = baseline[
            "execution_time_s"
        ]

        for result in group:
            speedup = (
                baseline_time
                /
                result[
                    "execution_time_s"
                ]
            )

            efficiency = (
                speedup
                /
                result[
                    "workers"
                ]
                *
                100.0
            )

            result[
                "speedup"
            ] = speedup

            result[
                "efficiency_percent"
            ] = efficiency


def print_summary(results):
    print()
    print(
        "=============================================================="
    )
    print(
        "Workload Scaling Benchmark"
    )
    print(
        "=============================================================="
    )

    print(
        f"{'Scenarios':<12}"
        f"{'Workers':<10}"
        f"{'Exec Time':<14}"
        f"{'Throughput':<16}"
        f"{'Speedup':<12}"
        f"{'Efficiency':<12}"
    )

    print(
        "-" * 76
    )

    for result in results:
        print(
            f"{result['scenario_count']:<12}"
            f"{result['workers']:<10}"
            f"{result['execution_time_s']:<14.3f}"
            f"{result['execution_throughput']:<16.2f}"
            f"{result.get('speedup', 0.0):<12.2f}"
            f"{result.get('efficiency_percent', 0.0):<12.2f}%"
        )

    print(
        "=============================================================="
    )

    print()
    print(
        f"CSV saved to: {CSV_PATH}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--counts",
        nargs="+",
        type=int,
        default=[
            100,
            500,
            1000,
            5000,
        ],
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

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
    )

    parser.add_argument(
        "--model-version",
        default="v3",
    )

    args = parser.parse_args()

    results = []

    with tempfile.TemporaryDirectory() as temp_root:
        temp_root = Path(
            temp_root
        )

        for count in args.counts:
            scenario_directory = (
                temp_root
                /
                f"scenarios_{count}"
            )

            print()
            print(
                f"Creating {count} benchmark scenarios..."
            )

            create_benchmark_dataset(
                count,
                scenario_directory,
            )

            for workers in args.workers:
                print(
                    f"Running {count} scenarios "
                    f"with {workers} worker(s)..."
                )

                result = run_factory(
                    scenario_directory,
                    count,
                    workers,
                    args.model_version,
                    args.duration,
                )

                results.append(
                    result
                )

                print(
                    "  Execution time: "
                    f"{result['execution_time_s']:.3f} s"
                )

                print(
                    "  Execution throughput: "
                    f"{result['execution_throughput']:.2f} simulations/s"
                )

    calculate_scaling(
        results
    )

    results.sort(
        key=lambda item: (
            item[
                "scenario_count"
            ],
            item[
                "workers"
            ],
        )
    )

    save_csv(
        results
    )

    print_summary(
        results
    )


if __name__ == "__main__":
    main()