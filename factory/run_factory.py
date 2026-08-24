import argparse
import json
import os
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from factory.database import generate_run_id
from factory.database import save_results
from factory.feasibility import evaluate_scenario_file
from factory.worker import run_scenario


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)

RESULTS_DIR = (
    ROOT
    / "results"
    / "runs"
)


def classify_failure(result):
    if result.get("status") == "ERROR":
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

    if abs(
        result.get(
            "final_gap_error",
            0.0,
        )
    ) > 5.0:
        return "gap_convergence"

    if abs(
        result.get(
            "final_relative_velocity",
            0.0,
        )
    ) > 0.5:
        return "velocity_convergence"

    return None


def classify_category(result):
    if result.get("status") == "ERROR":
        return "error"

    if result.get("status") == "PASS":
        return "pass"

    if result.get(
        "scenario_feasible"
    ) is False:
        return "infeasible_scenario"

    return "model_failure"


def create_temporary_scenario(
    source_path,
    duration,
    temp_directory,
):
    with open(
        source_path,
        "r",
        encoding="utf-8",
    ) as file:
        scenario = json.load(file)

    if duration is not None:
        scenario["duration"] = duration

    temporary_path = (
        Path(temp_directory)
        /
        source_path.name
    )

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            scenario,
            file,
            indent=2,
        )

    return temporary_path


def execute_factory(
    workers,
    model_version,
    duration,
    scenario_directory,
    save_database,
    quiet,
):
    scenario_directory = Path(
        scenario_directory
    )

    scenario_paths = sorted(
        scenario_directory.glob(
            "*.json"
        )
    )

    if not scenario_paths:
        raise RuntimeError(
            f"No JSON scenarios found in {scenario_directory}"
        )

    if save_database:
        run_id = generate_run_id()
    else:
        run_id = "benchmark"

    if not quiet:
        print()
        print(
            "============================================"
        )
        print(
            "Simulation Factory"
        )
        print(
            "============================================"
        )

        print(
            f"Run ID:                  {run_id}"
        )

        print(
            f"Model version:           {model_version}"
        )

        print(
            f"Workers:                 {workers}"
        )

        print(
            f"Scenarios:               {len(scenario_paths)}"
        )

        if duration is not None:
            print(
                f"Evaluation horizon:      {duration:.1f} s"
            )
        else:
            print(
                "Evaluation horizon:      scenario default"
            )

        print(
            "============================================"
        )

    preparation_start = time.perf_counter()

    with tempfile.TemporaryDirectory() as temp_directory:
        execution_paths = []
        feasibility_results = {}

        for source_path in scenario_paths:
            oracle = evaluate_scenario_file(
                source_path
            )

            feasibility_results[
                source_path.stem
            ] = oracle

            temporary_path = create_temporary_scenario(
                source_path,
                duration,
                temp_directory,
            )

            execution_paths.append(
                temporary_path
            )

        preparation_time = (
            time.perf_counter()
            -
            preparation_start
        )

        execution_start = time.perf_counter()

        with ProcessPoolExecutor(
            max_workers=workers
        ) as executor:
            results = list(
                executor.map(
                    run_scenario,
                    execution_paths,
                )
            )

        execution_time = (
            time.perf_counter()
            -
            execution_start
        )

    processing_start = time.perf_counter()

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

        result[
            "evaluation_duration"
        ] = duration

    processing_time = (
        time.perf_counter()
        -
        processing_start
    )

    if save_database:
        save_results(
            results,
            run_id,
            model_version,
        )

        RESULTS_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            RESULTS_DIR
            /
            f"{run_id}_{model_version}_full.json"
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
        result.get(
            "failure_category"
        ) == "pass"
        for result in results
    )

    model_failures = sum(
        result.get(
            "failure_category"
        ) == "model_failure"
        for result in results
    )

    infeasible = sum(
        result.get(
            "failure_category"
        ) == "infeasible_scenario"
        for result in results
    )

    errors = sum(
        result.get(
            "failure_category"
        ) == "error"
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

    feasible_total = (
        len(results)
        -
        infeasible
        -
        errors
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

    execution_throughput = (
        len(results)
        /
        execution_time
        if execution_time > 0.0
        else 0.0
    )

    internal_total_time = (
        preparation_time
        +
        execution_time
        +
        processing_time
    )

    total_throughput = (
        len(results)
        /
        internal_total_time
        if internal_total_time > 0.0
        else 0.0
    )

    summary = {
        "run_id": run_id,
        "model_version": model_version,
        "workers": workers,
        "scenario_count": len(results),
        "duration": duration,
        "passed": passed,
        "model_failures": model_failures,
        "infeasible": infeasible,
        "errors": errors,
        "collisions": collisions,
        "unsafe_gaps": unsafe_gaps,
        "feasible_pass_rate": feasible_pass_rate,
        "preparation_time_s": preparation_time,
        "execution_time_s": execution_time,
        "processing_time_s": processing_time,
        "internal_total_time_s": internal_total_time,
        "execution_throughput": execution_throughput,
        "total_throughput": total_throughput,
    }

    if not quiet:
        print()
        print(
            "============================================"
        )
        print(
            "Simulation Factory Summary"
        )
        print(
            "============================================"
        )

        print(
            f"Total scenarios:          {len(results)}"
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
            f"Feasible pass rate:       {feasible_pass_rate:.2f}%"
        )

        print()

        print(
            f"Preparation time:         {preparation_time:.3f} s"
        )

        print(
            f"Simulation execution:     {execution_time:.3f} s"
        )

        print(
            f"Result processing:        {processing_time:.3f} s"
        )

        print(
            f"Internal total:           {internal_total_time:.3f} s"
        )

        print()

        print(
            f"Execution throughput:     {execution_throughput:.2f} simulations/s"
        )

        print(
            f"Total throughput:         {total_throughput:.2f} simulations/s"
        )

        print(
            "============================================"
        )

    print(
        "FACTORY_SUMMARY="
        +
        json.dumps(
            summary,
            separators=(
                ",",
                ":",
            ),
        )
    )

    return summary


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count(),
    )

    parser.add_argument(
        "--model-version",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--scenario-dir",
        type=Path,
        default=DEFAULT_SCENARIO_DIR,
    )

    parser.add_argument(
        "--no-db",
        action="store_true",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
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

    if (
        args.duration is not None
        and
        args.duration <= 0.0
    ):
        raise ValueError(
            "Duration must be greater than zero."
        )

    execute_factory(
        args.workers,
        args.model_version,
        args.duration,
        args.scenario_dir,
        not args.no_db,
        args.quiet,
    )


if __name__ == "__main__":
    main()