import argparse
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    ROOT
    / "results"
    / "simulation_factory.db"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "reports"
)


def load_run(
    run_id,
):
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            scenario_id,
            status,
            failure_reason,
            failure_category,
            scenario_feasible,
            collision,
            unsafe_gap,
            minimum_gap,
            minimum_ttc,
            maximum_deceleration,
            final_gap_error,
            final_relative_velocity
        FROM simulation_runs
        WHERE run_id = ?
        ORDER BY scenario_id
        """,
        (
            run_id,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    if not rows:
        raise RuntimeError(
            f"No results found for {run_id}"
        )

    results = []

    for row in rows:
        results.append(
            {
                "scenario_id": row[0],
                "status": row[1],
                "failure_reason": row[2],
                "failure_category": row[3],
                "scenario_feasible": (
                    bool(row[4])
                    if row[4] is not None
                    else None
                ),
                "collision": bool(row[5]),
                "unsafe_gap": bool(row[6]),
                "minimum_gap": row[7],
                "minimum_ttc": row[8],
                "maximum_deceleration": row[9],
                "final_gap_error": row[10],
                "final_relative_velocity": row[11],
            }
        )

    return results


def plot_outcomes(
    results,
    run_id,
):
    categories = [
        "Pass",
        "Model failure",
        "Infeasible",
        "Error",
    ]

    counts = [
        sum(
            result[
                "failure_category"
            ]
            ==
            "pass"
            for result in results
        ),
        sum(
            result[
                "failure_category"
            ]
            ==
            "model_failure"
            for result in results
        ),
        sum(
            result[
                "failure_category"
            ]
            ==
            "infeasible_scenario"
            for result in results
        ),
        sum(
            result[
                "failure_category"
            ]
            ==
            "error"
            for result in results
        ),
    ]

    plt.figure(
        figsize=(8, 5)
    )

    bars = plt.bar(
        categories,
        counts,
    )

    plt.xlabel(
        "Result category"
    )

    plt.ylabel(
        "Scenario count"
    )

    plt.title(
        f"Simulation Outcomes - {run_id}"
    )

    plt.ylim(
        0,
        max(counts) * 1.15
        if max(counts) > 0
        else 1,
    )

    for bar, count in zip(
        bars,
        counts,
    ):
        plt.text(
            bar.get_x()
            +
            bar.get_width()
            /
            2,
            bar.get_height()
            +
            0.5,
            str(count),
            ha="center",
        )

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        f"{run_id}_outcomes.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def plot_minimum_gap(
    results,
    run_id,
):
    sorted_results = sorted(
        results,
        key=lambda result: (
            result[
                "minimum_gap"
            ]
            if result[
                "minimum_gap"
            ]
            is not None
            else float("inf")
        ),
    )

    scenario_ids = [
        result[
            "scenario_id"
        ]
        for result in sorted_results
    ]

    minimum_gaps = [
        result[
            "minimum_gap"
        ]
        for result in sorted_results
    ]

    plt.figure(
        figsize=(12, 6)
    )

    plt.plot(
        range(
            len(
                minimum_gaps
            )
        ),
        minimum_gaps,
        marker=".",
        linestyle="none",
    )

    plt.axhline(
        0.0,
        linestyle="--",
        label="Collision boundary",
    )

    plt.xlabel(
        "Scenarios sorted by minimum gap"
    )

    plt.ylabel(
        "Minimum observed gap (m)"
    )

    plt.title(
        f"Minimum Gap Distribution - {run_id}"
    )

    plt.legend()

    plt.grid(
        True,
        alpha=0.3,
    )

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        f"{run_id}_minimum_gap_distribution.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def plot_ttc_vs_gap(
    results,
    run_id,
):
    valid_results = [
        result
        for result in results
        if (
            result[
                "minimum_ttc"
            ]
            is not None
            and
            result[
                "minimum_ttc"
            ]
            >=
            0.0
            and
            result[
                "minimum_gap"
            ]
            is not None
        )
    ]

    feasible_results = [
        result
        for result in valid_results
        if result[
            "scenario_feasible"
        ]
        is True
    ]

    infeasible_results = [
        result
        for result in valid_results
        if result[
            "scenario_feasible"
        ]
        is False
    ]

    plt.figure(
        figsize=(8, 6)
    )

    if feasible_results:
        plt.scatter(
            [
                result[
                    "minimum_ttc"
                ]
                for result in feasible_results
            ],
            [
                result[
                    "minimum_gap"
                ]
                for result in feasible_results
            ],
            label="Feasible",
            alpha=0.7,
        )

    if infeasible_results:
        plt.scatter(
            [
                result[
                    "minimum_ttc"
                ]
                for result in infeasible_results
            ],
            [
                result[
                    "minimum_gap"
                ]
                for result in infeasible_results
            ],
            label="Infeasible",
            marker="x",
        )

    plt.axhline(
        0.0,
        linestyle="--",
        label="Collision boundary",
    )

    plt.xlabel(
        "Minimum TTC (s)"
    )

    plt.ylabel(
        "Minimum observed gap (m)"
    )

    plt.title(
        f"Safety Margin: TTC vs Minimum Gap - {run_id}"
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
        f"{run_id}_ttc_vs_gap.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def plot_infeasible_scenarios(
    results,
    run_id,
):
    infeasible = [
        result
        for result in results
        if result[
            "failure_category"
        ]
        ==
        "infeasible_scenario"
    ]

    infeasible.sort(
        key=lambda result: result[
            "minimum_gap"
        ]
    )

    if not infeasible:
        return None

    scenario_ids = [
        result[
            "scenario_id"
        ]
        for result in infeasible
    ]

    gaps = [
        result[
            "minimum_gap"
        ]
        for result in infeasible
    ]

    plt.figure(
        figsize=(9, 5)
    )

    bars = plt.bar(
        scenario_ids,
        gaps,
    )

    plt.axhline(
        0.0,
        linestyle="--",
        label="Collision boundary",
    )

    plt.xlabel(
        "Scenario"
    )

    plt.ylabel(
        "Minimum observed gap (m)"
    )

    plt.title(
        f"Infeasible Scenario Safety Results - {run_id}"
    )

    plt.xticks(
        rotation=45,
        ha="right",
    )

    for bar, gap in zip(
        bars,
        gaps,
    ):
        plt.text(
            bar.get_x()
            +
            bar.get_width()
            /
            2,
            gap,
            f"{gap:.2f}",
            ha="center",
            va=(
                "bottom"
                if gap >= 0.0
                else "top"
            ),
        )

    plt.legend()

    plt.tight_layout()

    output_path = (
        OUTPUT_DIR
        /
        f"{run_id}_infeasible_scenarios.png"
    )

    plt.savefig(
        output_path,
        dpi=200,
    )

    plt.close()

    return output_path


def print_summary(
    results,
    run_id,
):
    passed = sum(
        result[
            "failure_category"
        ]
        ==
        "pass"
        for result in results
    )

    model_failures = sum(
        result[
            "failure_category"
        ]
        ==
        "model_failure"
        for result in results
    )

    infeasible = sum(
        result[
            "failure_category"
        ]
        ==
        "infeasible_scenario"
        for result in results
    )

    collisions = sum(
        result[
            "collision"
        ]
        for result in results
    )

    unsafe_gaps = sum(
        result[
            "unsafe_gap"
        ]
        for result in results
    )

    feasible_total = sum(
        result[
            "scenario_feasible"
        ]
        is True
        for result in results
    )

    feasible_pass_rate = (
        passed
        /
        feasible_total
        *
        100.0
        if feasible_total > 0
        else 0.0
    )

    print()
    print(
        "============================================"
    )
    print(
        "Safety Analysis"
    )
    print(
        "============================================"
    )

    print(
        f"Run:                    {run_id}"
    )

    print(
        f"Total scenarios:        {len(results)}"
    )

    print(
        f"Passed:                 {passed}"
    )

    print(
        f"Model failures:         {model_failures}"
    )

    print(
        f"Infeasible scenarios:   {infeasible}"
    )

    print(
        f"Collisions:             {collisions}"
    )

    print(
        f"Unsafe gaps:            {unsafe_gaps}"
    )

    print(
        f"Feasible scenarios:     {feasible_total}"
    )

    print(
        f"Feasible pass rate:     {feasible_pass_rate:.2f}%"
    )

    print(
        "============================================"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--run-id",
        default="run_007",
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = load_run(
        args.run_id
    )

    print_summary(
        results,
        args.run_id,
    )

    output_paths = [
        plot_outcomes(
            results,
            args.run_id,
        ),
        plot_minimum_gap(
            results,
            args.run_id,
        ),
        plot_ttc_vs_gap(
            results,
            args.run_id,
        ),
        plot_infeasible_scenarios(
            results,
            args.run_id,
        ),
    ]

    print()
    print(
        "Safety plots generated:"
    )

    for path in output_paths:
        if path is not None:
            print(
                path
            )


if __name__ == "__main__":
    main()