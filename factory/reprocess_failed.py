import argparse
import json
import os
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from factory.database import DATABASE_PATH
from factory.database import generate_run_id
from factory.database import save_results
from factory.feasibility import evaluate_scenario_file
from factory.worker import run_scenario


ROOT = Path(__file__).resolve().parents[1]

SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)

OUTPUT_DIR = (
    ROOT
    / "results"
    / "runs"
)


def get_latest_run_id():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT run_id
        FROM simulation_runs
        ORDER BY id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        raise RuntimeError(
            "No simulation runs found."
        )

    return row[0]


def load_failed_scenarios(
    source_run_id,
):
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT scenario_id
        FROM simulation_runs
        WHERE run_id = ?
          AND status != 'PASS'
        ORDER BY scenario_id
        """,
        (
            source_run_id,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


def classify_failure(
    result,
):
    if (
        result.get(
            "status"
        )
        ==
        "ERROR"
    ):
        return "simulation_error"

    if result.get(
        "collision",
        False,
    ):
        return "collision"

    if result.get(
        "unsafe_gap",
        False,
    ):
        return "unsafe_gap"

    if (
        abs(
            result.get(
                "final_gap_error",
                0.0,
            )
        )
        >
        5.0
    ):
        return "gap_convergence"

    if (
        abs(
            result.get(
                "final_relative_velocity",
                0.0,
            )
        )
        >
        0.5
    ):
        return "velocity_convergence"

    return None


def classify_category(
    result,
):
    if (
        result.get(
            "status"
        )
        ==
        "ERROR"
    ):
        return "error"

    if (
        result.get(
            "status"
        )
        ==
        "PASS"
    ):
        return "pass"

    if (
        result.get(
            "scenario_feasible"
        )
        is False
    ):
        return "infeasible_scenario"

    return "model_failure"


def run_failed_scenarios(
    workers,
    source_run_id,
    model_version,
):
    failed_ids = load_failed_scenarios(
        source_run_id
    )

    if not failed_ids:
        print(
            "No failed scenarios found."
        )
        return

    scenario_paths = [
        SCENARIO_DIR
        /
        f"{scenario_id}.json"
        for scenario_id in failed_ids
    ]

    missing_paths = [
        path
        for path in scenario_paths
        if not path.exists()
    ]

    if missing_paths:
        raise RuntimeError(
            f"{len(missing_paths)} scenario files are missing."
        )

    feasibility_results = {}

    for path in scenario_paths:
        feasibility_results[
            path.stem
        ] = evaluate_scenario_file(
            path
        )

    run_id = generate_run_id()

    start_time = time.perf_counter()

    with ProcessPoolExecutor(
        max_workers=workers
    ) as executor:
        results = list(
            executor.map(
                run_scenario,
                scenario_paths,
            )
        )

    runtime = (
        time.perf_counter()
        -
        start_time
    )

    for result in results:
        scenario_id = result[
            "scenario_id"
        ]

        oracle = feasibility_results[
            scenario_id
        ]

        result[
            "scenario_feasible"
        ] = oracle[
            "feasible"
        ]

        result[
            "oracle_collision"
        ] = oracle[
            "oracle_collision"
        ]

        result[
            "oracle_unsafe_gap"
        ] = oracle[
            "oracle_unsafe_gap"
        ]

        result[
            "oracle_minimum_gap"
        ] = oracle[
            "oracle_minimum_gap"
        ]

        result[
            "failure_reason"
        ] = classify_failure(
            result
        )

        result[
            "failure_category"
        ] = classify_category(
            result
        )

    save_results(
        results,
        run_id,
        model_version,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        /
        f"{run_id}_{model_version}.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
        )

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

    errors = sum(
        result[
            "failure_category"
        ]
        ==
        "error"
        for result in results
    )

    collisions = sum(
        result.get(
            "collision",
            False,
        )
        for result in results
    )

    unsafe_gaps = sum(
        result.get(
            "unsafe_gap",
            False,
        )
        for result in results
    )

    gap_convergence = sum(
        result.get(
            "failure_reason"
        )
        ==
        "gap_convergence"
        and
        result.get(
            "scenario_feasible"
        )
        is True
        for result in results
    )

    velocity_convergence = sum(
        result.get(
            "failure_reason"
        )
        ==
        "velocity_convergence"
        and
        result.get(
            "scenario_feasible"
        )
        is True
        for result in results
    )

    throughput = (
        len(results)
        /
        runtime
        if runtime > 0.0
        else 0.0
    )

    print()
    print(
        "============================================"
    )
    print(
        "Failure Reprocessing + Feasibility"
    )
    print(
        "============================================"
    )

    print(
        f"Source run:               {source_run_id}"
    )

    print(
        f"New run:                  {run_id}"
    )

    print(
        f"Model version:            {model_version}"
    )

    print()

    print(
        f"Scenarios processed:      {len(results)}"
    )

    print(
        f"Passed:                   {passed}"
    )

    print(
        f"Model failures:           {model_failures}"
    )

    print(
        f"Infeasible scenarios:     {infeasible}"
    )

    print(
        f"Errors:                   {errors}"
    )

    print()

    print(
        f"Observed collisions:      {collisions}"
    )

    print(
        f"Observed unsafe gaps:     {unsafe_gaps}"
    )

    print()

    print(
        f"Feasible gap failures:    {gap_convergence}"
    )

    print(
        f"Feasible velocity fails:  {velocity_convergence}"
    )

    print()

    print(
        f"Runtime:                  {runtime:.3f} s"
    )

    print(
        f"Throughput:               {throughput:.2f} simulations/s"
    )

    print(
        "============================================"
    )

    print(
        f"Results saved to: {output_path}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count(),
    )

    parser.add_argument(
        "--source-run",
        type=str,
        default=None,
    )

    parser.add_argument(
        "--model-version",
        type=str,
        required=True,
    )

    args = parser.parse_args()

    if (
        args.workers is None
        or
        args.workers <= 0
    ):
        raise ValueError(
            "Worker count must be greater than zero."
        )

    source_run_id = (
        args.source_run
        if args.source_run
        else get_latest_run_id()
    )

    run_failed_scenarios(
        args.workers,
        source_run_id,
        args.model_version,
    )


if __name__ == "__main__":
    main()