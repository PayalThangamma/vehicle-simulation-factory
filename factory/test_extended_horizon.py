import argparse
import json
import sqlite3
import subprocess
import tempfile
from pathlib import Path

from database import DATABASE_PATH


ROOT = Path(__file__).resolve().parents[1]

SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)

EXECUTABLE = (
    ROOT
    / "build"
    / "simulation_runner.exe"
)


def load_model_failures(
    run_id,
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
          AND failure_category = 'model_failure'
        ORDER BY scenario_id
        """,
        (
            run_id,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


def run_extended_scenario(
    scenario_id,
    duration,
):
    source_path = (
        SCENARIO_DIR
        /
        f"{scenario_id}.json"
    )

    with open(
        source_path,
        "r",
        encoding="utf-8",
    ) as file:
        scenario = json.load(
            file
        )

    original_duration = scenario[
        "duration"
    ]

    scenario[
        "duration"
    ] = duration

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        json.dump(
            scenario,
            temp_file,
            indent=2,
        )

        temp_path = Path(
            temp_file.name
        )

    try:
        process = subprocess.run(
            [
                str(EXECUTABLE),
                str(temp_path),
            ],
            capture_output=True,
            text=True,
        )

        if process.returncode != 0:
            return {
                "scenario_id": scenario_id,
                "status": "ERROR",
                "error": process.stderr.strip(),
            }

        result = json.loads(
            process.stdout.strip()
        )

        result[
            "original_duration"
        ] = original_duration

        result[
            "extended_duration"
        ] = duration

        return result

    finally:
        temp_path.unlink(
            missing_ok=True
        )


def classify_convergence(
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

    gap_error = abs(
        result[
            "final_gap_error"
        ]
    )

    relative_velocity = abs(
        result[
            "final_relative_velocity"
        ]
    )

    if (
        gap_error <= 5.0
        and
        relative_velocity <= 0.5
        and
        not result[
            "collision"
        ]
        and
        not result[
            "unsafe_gap"
        ]
    ):
        return "converged"

    if gap_error > 5.0:
        return "gap_convergence"

    if relative_velocity > 0.5:
        return "velocity_convergence"

    return "other_failure"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-run",
        required=True,
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
    )

    args = parser.parse_args()

    scenario_ids = load_model_failures(
        args.source_run
    )

    if not scenario_ids:
        print(
            "No model failures found."
        )
        return

    results = []

    print()
    print(
        "============================================"
    )
    print(
        "Extended Horizon Diagnostic"
    )
    print(
        "============================================"
    )

    print(
        f"Source run:       {args.source_run}"
    )

    print(
        f"New duration:     {args.duration:.1f} s"
    )

    print(
        f"Scenarios:        {len(scenario_ids)}"
    )

    print(
        "============================================"
    )

    for scenario_id in scenario_ids:
        result = run_extended_scenario(
            scenario_id,
            args.duration,
        )

        category = classify_convergence(
            result
        )

        result[
            "diagnostic_category"
        ] = category

        results.append(
            result
        )

        print()
        print(
            f"Scenario:          {scenario_id}"
        )

        if (
            result.get(
                "status"
            )
            ==
            "ERROR"
        ):
            print(
                "Status:            ERROR"
            )

            print(
                f"Error:             {result['error']}"
            )

            continue

        print(
            f"Status:            {result['status']}"
        )

        print(
            f"Category:          {category}"
        )

        print(
            "Final gap error:   "
            f"{result['final_gap_error']:.4f} m"
        )

        print(
            "Relative velocity: "
            f"{result['final_relative_velocity']:.4f} m/s"
        )

        print(
            "Minimum gap:       "
            f"{result['minimum_gap']:.4f} m"
        )

        print(
            "--------------------------------------------"
        )

    converged = sum(
        result.get(
            "diagnostic_category"
        )
        ==
        "converged"
        for result in results
    )

    gap_failures = sum(
        result.get(
            "diagnostic_category"
        )
        ==
        "gap_convergence"
        for result in results
    )

    velocity_failures = sum(
        result.get(
            "diagnostic_category"
        )
        ==
        "velocity_convergence"
        for result in results
    )

    errors = sum(
        result.get(
            "diagnostic_category"
        )
        ==
        "error"
        for result in results
    )

    print()
    print(
        "============================================"
    )
    print(
        "Extended Horizon Summary"
    )
    print(
        "============================================"
    )

    print(
        f"Scenarios tested:          {len(results)}"
    )

    print(
        f"Converged:                 {converged}"
    )

    print(
        f"Gap convergence failures:  {gap_failures}"
    )

    print(
        f"Velocity failures:         {velocity_failures}"
    )

    print(
        f"Errors:                    {errors}"
    )

    print(
        "============================================"
    )


if __name__ == "__main__":
    main()