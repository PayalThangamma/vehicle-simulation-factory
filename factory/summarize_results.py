import argparse
import sqlite3
from pathlib import Path

from database import DATABASE_PATH


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
            collision,
            unsafe_gap,
            minimum_gap,
            minimum_ttc,
            maximum_deceleration,
            final_gap_error,
            final_relative_velocity,
            runtime_ms
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

    results = {}

    for row in rows:
        results[
            row[0]
        ] = {
            "status": row[1],
            "failure_reason": row[2],
            "collision": bool(
                row[3]
            ),
            "unsafe_gap": bool(
                row[4]
            ),
            "minimum_gap": row[5],
            "minimum_ttc": row[6],
            "maximum_deceleration": row[7],
            "final_gap_error": row[8],
            "final_relative_velocity": row[9],
            "runtime_ms": row[10],
        }

    return results


def list_runs():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            run_id,
            model_version,
            COUNT(*) AS scenario_count,
            SUM(
                CASE
                    WHEN status = 'PASS'
                    THEN 1
                    ELSE 0
                END
            ) AS passed_count,
            SUM(
                CASE
                    WHEN status = 'FAIL'
                    THEN 1
                    ELSE 0
                END
            ) AS failed_count,
            SUM(
                CASE
                    WHEN status = 'ERROR'
                    THEN 1
                    ELSE 0
                END
            ) AS error_count,
            AVG(runtime_ms) AS average_runtime_ms
        FROM simulation_runs
        GROUP BY
            run_id,
            model_version
        ORDER BY run_id
        """
    )

    rows = cursor.fetchall()

    connection.close()

    print()
    print(
        "============================================"
    )
    print(
        "Simulation Factory Runs"
    )
    print(
        "============================================"
    )

    for row in rows:
        print(
            f"{row[0]:<10} "
            f"{row[1]:<8} "
            f"scenarios={row[2]:<5} "
            f"pass={row[3]:<5} "
            f"fail={row[4]:<5} "
            f"error={row[5]:<5} "
            f"avg_runtime={row[6]:.4f} ms"
        )

    print(
        "============================================"
    )


def compare_runs(
    baseline_run,
    candidate_run,
):
    baseline = load_run(
        baseline_run
    )

    candidate = load_run(
        candidate_run
    )

    common_ids = sorted(
        set(
            baseline.keys()
        )
        &
        set(
            candidate.keys()
        )
    )

    if not common_ids:
        raise RuntimeError(
            "The selected runs have no common scenarios."
        )

    improved = []

    regressed = []

    persistent_failures = []

    persistent_passes = []

    changed_failure_reason = []

    gap_improved = []

    gap_regressed = []

    runtime_changes = []

    for scenario_id in common_ids:
        old = baseline[
            scenario_id
        ]

        new = candidate[
            scenario_id
        ]

        old_pass = (
            old["status"]
            ==
            "PASS"
        )

        new_pass = (
            new["status"]
            ==
            "PASS"
        )

        if (
            not old_pass
            and
            new_pass
        ):
            improved.append(
                scenario_id
            )

        elif (
            old_pass
            and
            not new_pass
        ):
            regressed.append(
                scenario_id
            )

        elif (
            not old_pass
            and
            not new_pass
        ):
            persistent_failures.append(
                scenario_id
            )

        else:
            persistent_passes.append(
                scenario_id
            )

        if (
            old["failure_reason"]
            !=
            new["failure_reason"]
        ):
            changed_failure_reason.append(
                scenario_id
            )

        old_gap_error = abs(
            old[
                "final_gap_error"
            ]
        )

        new_gap_error = abs(
            new[
                "final_gap_error"
            ]
        )

        if (
            new_gap_error
            <
            old_gap_error
        ):
            gap_improved.append(
                scenario_id
            )

        elif (
            new_gap_error
            >
            old_gap_error
        ):
            gap_regressed.append(
                scenario_id
            )

        old_runtime = (
            old[
                "runtime_ms"
            ]
        )

        new_runtime = (
            new[
                "runtime_ms"
            ]
        )

        if (
            old_runtime is not None
            and
            new_runtime is not None
        ):
            runtime_changes.append(
                new_runtime
                -
                old_runtime
            )

    baseline_passes = sum(
        result[
            "status"
        ]
        ==
        "PASS"
        for result in baseline.values()
    )

    candidate_passes = sum(
        result[
            "status"
        ]
        ==
        "PASS"
        for result in candidate.values()
    )

    baseline_collisions = sum(
        result[
            "collision"
        ]
        for result in baseline.values()
    )

    candidate_collisions = sum(
        result[
            "collision"
        ]
        for result in candidate.values()
    )

    baseline_unsafe = sum(
        result[
            "unsafe_gap"
        ]
        for result in baseline.values()
    )

    candidate_unsafe = sum(
        result[
            "unsafe_gap"
        ]
        for result in candidate.values()
    )

    average_runtime_change = (
        sum(
            runtime_changes
        )
        /
        len(
            runtime_changes
        )
        if runtime_changes
        else 0.0
    )

    print()
    print(
        "============================================"
    )
    print(
        "Simulation Run Comparison"
    )
    print(
        "============================================"
    )

    print(
        f"Baseline run:       {baseline_run}"
    )

    print(
        f"Candidate run:      {candidate_run}"
    )

    print(
        f"Common scenarios:   {len(common_ids)}"
    )

    print()

    print(
        "PASS / FAIL"
    )

    print(
        "--------------------------------------------"
    )

    print(
        f"Baseline passes:    {baseline_passes}"
    )

    print(
        f"Candidate passes:   {candidate_passes}"
    )

    print(
        f"Improved scenarios: {len(improved)}"
    )

    print(
        f"Regressed scenarios:{len(regressed)}"
    )

    print(
        f"Persistent failures:{len(persistent_failures)}"
    )

    print()

    print(
        "SAFETY"
    )

    print(
        "--------------------------------------------"
    )

    print(
        f"Baseline collisions:{baseline_collisions}"
    )

    print(
        f"Candidate collisions:{candidate_collisions}"
    )

    print(
        f"Baseline unsafe gaps:{baseline_unsafe}"
    )

    print(
        f"Candidate unsafe gaps:{candidate_unsafe}"
    )

    print()

    print(
        "QUALITY"
    )

    print(
        "--------------------------------------------"
    )

    print(
        f"Gap error improved: {len(gap_improved)}"
    )

    print(
        f"Gap error regressed:{len(gap_regressed)}"
    )

    print(
        f"Failure reason changed:"
        f"{len(changed_failure_reason)}"
    )

    print()

    print(
        "PERFORMANCE"
    )

    print(
        "--------------------------------------------"
    )

    print(
        "Average runtime delta: "
        f"{average_runtime_change:+.6f} ms"
    )

    print(
        "============================================"
    )

    if improved:
        print()
        print(
            "Improved scenarios:"
        )

        for scenario_id in improved:
            print(
                f"  {scenario_id}"
            )

    if regressed:
        print()
        print(
            "Regressed scenarios:"
        )

        for scenario_id in regressed:
            print(
                f"  {scenario_id}"
            )

    if persistent_failures:
        print()
        print(
            "Persistent failures:"
        )

        for scenario_id in persistent_failures:
            print(
                f"  {scenario_id}"
            )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--list-runs",
        action="store_true",
    )

    parser.add_argument(
        "--baseline",
        type=str,
    )

    parser.add_argument(
        "--candidate",
        type=str,
    )

    args = parser.parse_args()

    if args.list_runs:
        list_runs()
        return

    if (
        args.baseline
        and
        args.candidate
    ):
        compare_runs(
            args.baseline,
            args.candidate,
        )
        return

    parser.error(
        "Use --list-runs or provide both "
        "--baseline and --candidate."
    )


if __name__ == "__main__":
    main()