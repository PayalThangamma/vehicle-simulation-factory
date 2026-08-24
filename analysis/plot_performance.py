import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    ROOT
    / "results"
    / "reports"
    / "scaling_benchmark.csv"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "reports"
)


def load_results():
    rows = []

    with open(
        CSV_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(
                {
                    "scenario_count": int(
                        row["scenario_count"]
                    ),
                    "workers": int(
                        row["workers"]
                    ),
                    "execution_time_s": float(
                        row["execution_time_s"]
                    ),
                    "execution_throughput": float(
                        row["execution_throughput"]
                    ),
                    "speedup": float(
                        row["speedup"]
                    ),
                    "efficiency_percent": float(
                        row["efficiency_percent"]
                    ),
                }
            )

    return rows


def plot_throughput(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[
            row["scenario_count"]
        ].append(row)

    plt.figure(
        figsize=(8, 5)
    )

    for scenario_count in sorted(
        grouped
    ):
        group = sorted(
            grouped[
                scenario_count
            ],
            key=lambda item: item[
                "workers"
            ],
        )

        workers = [
            item["workers"]
            for item in group
        ]

        throughput = [
            item[
                "execution_throughput"
            ]
            for item in group
        ]

        plt.plot(
            workers,
            throughput,
            marker="o",
            label=f"{scenario_count} scenarios",
        )

    plt.xlabel(
        "Worker processes"
    )

    plt.ylabel(
        "Throughput (simulations/s)"
    )

    plt.title(
        "Simulation Factory Throughput Scaling"
    )

    plt.xticks(
        [1, 2, 4, 8]
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend()

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        "throughput_scaling.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def plot_speedup(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[
            row["scenario_count"]
        ].append(row)

    plt.figure(
        figsize=(8, 5)
    )

    for scenario_count in sorted(
        grouped
    ):
        group = sorted(
            grouped[
                scenario_count
            ],
            key=lambda item: item[
                "workers"
            ],
        )

        workers = [
            item["workers"]
            for item in group
        ]

        speedup = [
            item["speedup"]
            for item in group
        ]

        plt.plot(
            workers,
            speedup,
            marker="o",
            label=f"{scenario_count} scenarios",
        )

    ideal_workers = [
        1,
        2,
        4,
        8,
    ]

    plt.plot(
        ideal_workers,
        ideal_workers,
        linestyle="--",
        label="Ideal scaling",
    )

    plt.xlabel(
        "Worker processes"
    )

    plt.ylabel(
        "Speedup"
    )

    plt.title(
        "Simulation Factory Parallel Speedup"
    )

    plt.xticks(
        [1, 2, 4, 8]
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend()

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        "parallel_speedup.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def plot_efficiency(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[
            row["scenario_count"]
        ].append(row)

    plt.figure(
        figsize=(8, 5)
    )

    for scenario_count in sorted(
        grouped
    ):
        group = sorted(
            grouped[
                scenario_count
            ],
            key=lambda item: item[
                "workers"
            ],
        )

        workers = [
            item["workers"]
            for item in group
        ]

        efficiency = [
            item[
                "efficiency_percent"
            ]
            for item in group
        ]

        plt.plot(
            workers,
            efficiency,
            marker="o",
            label=f"{scenario_count} scenarios",
        )

    plt.xlabel(
        "Worker processes"
    )

    plt.ylabel(
        "Parallel efficiency (%)"
    )

    plt.title(
        "Simulation Factory Parallel Efficiency"
    )

    plt.xticks(
        [1, 2, 4, 8]
    )

    plt.ylim(
        0,
        105,
    )

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.legend()

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        "parallel_efficiency.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = load_results()

    throughput_path = plot_throughput(
        rows
    )

    speedup_path = plot_speedup(
        rows
    )

    efficiency_path = plot_efficiency(
        rows
    )

    print()
    print(
        "Performance plots generated:"
    )

    print(
        throughput_path
    )

    print(
        speedup_path
    )

    print(
        efficiency_path
    )


if __name__ == "__main__":
    main()