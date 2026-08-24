import json
import sqlite3
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

FACTORY_DIR = ROOT / "factory"

if str(FACTORY_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(FACTORY_DIR),
    )


import database
from feasibility import evaluate_scenario
from feasibility import evaluate_scenario_file
from run_factory import classify_category
from run_factory import classify_failure
from worker import run_scenario


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


def test_classify_pass():
    result = {
        "status": "PASS",
        "collision": False,
        "unsafe_gap": False,
        "final_gap_error": 0.1,
        "final_relative_velocity": 0.1,
    }

    assert classify_failure(
        result
    ) is None


def test_classify_collision():
    result = {
        "status": "FAIL",
        "collision": True,
        "unsafe_gap": True,
        "final_gap_error": 0.0,
        "final_relative_velocity": 0.0,
    }

    assert (
        classify_failure(
            result
        )
        ==
        "collision"
    )


def test_classify_unsafe_gap():
    result = {
        "status": "FAIL",
        "collision": False,
        "unsafe_gap": True,
        "final_gap_error": 0.0,
        "final_relative_velocity": 0.0,
    }

    assert (
        classify_failure(
            result
        )
        ==
        "unsafe_gap"
    )


def test_classify_gap_convergence():
    result = {
        "status": "FAIL",
        "collision": False,
        "unsafe_gap": False,
        "final_gap_error": 6.0,
        "final_relative_velocity": 0.1,
    }

    assert (
        classify_failure(
            result
        )
        ==
        "gap_convergence"
    )


def test_classify_velocity_convergence():
    result = {
        "status": "FAIL",
        "collision": False,
        "unsafe_gap": False,
        "final_gap_error": 1.0,
        "final_relative_velocity": 0.8,
    }

    assert (
        classify_failure(
            result
        )
        ==
        "velocity_convergence"
    )


def test_classify_simulation_error():
    result = {
        "status": "ERROR",
    }

    assert (
        classify_failure(
            result
        )
        ==
        "simulation_error"
    )


def test_failure_category_pass():
    result = {
        "status": "PASS",
        "scenario_feasible": True,
    }

    assert (
        classify_category(
            result
        )
        ==
        "pass"
    )


def test_failure_category_model_failure():
    result = {
        "status": "FAIL",
        "scenario_feasible": True,
    }

    assert (
        classify_category(
            result
        )
        ==
        "model_failure"
    )


def test_failure_category_infeasible():
    result = {
        "status": "FAIL",
        "scenario_feasible": False,
    }

    assert (
        classify_category(
            result
        )
        ==
        "infeasible_scenario"
    )


def test_failure_category_error():
    result = {
        "status": "ERROR",
        "scenario_feasible": None,
    }

    assert (
        classify_category(
            result
        )
        ==
        "error"
    )


def test_feasibility_oracle_safe_scenario():
    scenario = {
        "ego_initial_position": 0.0,
        "ego_initial_velocity": 10.0,
        "lead_initial_position": 50.0,
        "lead_initial_velocity": 15.0,
        "minimum_acceleration": -5.0,
        "lead_brake_start": 5.0,
        "lead_brake_duration": 1.0,
        "lead_brake_acceleration": -2.0,
        "minimum_gap": 5.0,
        "duration": 15.0,
        "dt": 0.01,
    }

    result = evaluate_scenario(
        scenario
    )

    assert (
        result[
            "feasible"
        ]
        is True
    )

    assert (
        result[
            "oracle_collision"
        ]
        is False
    )

    assert (
        result[
            "oracle_unsafe_gap"
        ]
        is False
    )


def test_feasibility_oracle_infeasible_scenario():
    scenario = {
        "ego_initial_position": 0.0,
        "ego_initial_velocity": 30.0,
        "lead_initial_position": 10.0,
        "lead_initial_velocity": 5.0,
        "minimum_acceleration": -5.0,
        "lead_brake_start": 2.0,
        "lead_brake_duration": 2.0,
        "lead_brake_acceleration": -4.0,
        "minimum_gap": 5.0,
        "duration": 15.0,
        "dt": 0.01,
    }

    result = evaluate_scenario(
        scenario
    )

    assert (
        result[
            "feasible"
        ]
        is False
    )

    assert (
        result[
            "oracle_unsafe_gap"
        ]
        is True
    )


def test_scenario_files_exist():
    scenario_paths = sorted(
        SCENARIO_DIR.glob(
            "*.json"
        )
    )

    assert (
        len(
            scenario_paths
        )
        ==
        100
    )


def test_scenario_json_structure():
    scenario_path = (
        SCENARIO_DIR
        /
        "acc_00001.json"
    )

    assert scenario_path.exists()

    with open(
        scenario_path,
        "r",
        encoding="utf-8",
    ) as file:
        scenario = json.load(
            file
        )

    required_fields = {
        "scenario_id",
        "ego_initial_position",
        "ego_initial_velocity",
        "lead_initial_position",
        "lead_initial_velocity",
        "desired_time_headway",
        "minimum_gap",
        "gap_kp",
        "relative_velocity_kp",
        "closing_speed_gain",
        "minimum_acceleration",
        "maximum_acceleration",
        "lead_brake_start",
        "lead_brake_duration",
        "lead_brake_acceleration",
        "duration",
        "dt",
    }

    assert required_fields.issubset(
        scenario.keys()
    )


def test_validated_dataset_feasibility():
    scenario_paths = sorted(
        SCENARIO_DIR.glob(
            "*.json"
        )
    )

    assert (
        len(
            scenario_paths
        )
        ==
        100
    )

    feasible = 0
    infeasible = 0

    for scenario_path in scenario_paths:
        result = evaluate_scenario_file(
            scenario_path
        )

        if result[
            "feasible"
        ]:
            feasible += 1
        else:
            infeasible += 1

    assert feasible == 94
    assert infeasible == 6


@pytest.mark.skipif(
    not EXECUTABLE.exists(),
    reason="Simulation executable has not been built.",
)
def test_simulation_runner_executes():
    scenario_path = (
        SCENARIO_DIR
        /
        "acc_00008.json"
    )

    result = run_scenario(
        scenario_path
    )

    assert (
        result[
            "scenario_id"
        ]
        ==
        "acc_00008"
    )

    assert result[
        "status"
    ] in {
        "PASS",
        "FAIL",
    }

    assert (
        "runtime_ms"
        in result
    )


@pytest.mark.skipif(
    not EXECUTABLE.exists(),
    reason="Simulation executable has not been built.",
)
def test_simulation_is_deterministic():
    scenario_path = (
        SCENARIO_DIR
        /
        "acc_00008.json"
    )

    first = run_scenario(
        scenario_path
    )

    second = run_scenario(
        scenario_path
    )

    deterministic_fields = [
        "scenario_id",
        "status",
        "collision",
        "unsafe_gap",
        "minimum_gap",
        "minimum_ttc",
        "maximum_deceleration",
        "final_gap_error",
        "final_relative_velocity",
    ]

    for field in deterministic_fields:
        assert (
            first[field]
            ==
            second[field]
        )


def test_database_write_and_read(
    tmp_path,
    monkeypatch,
):
    temporary_database = (
        tmp_path
        /
        "simulation_factory_test.db"
    )

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        temporary_database,
    )

    result = {
        "scenario_id": "test_001",
        "status": "PASS",
        "failure_reason": None,
        "collision": False,
        "unsafe_gap": False,
        "minimum_gap": 12.5,
        "minimum_ttc": 4.2,
        "maximum_deceleration": -2.0,
        "final_gap_error": 0.1,
        "final_relative_velocity": 0.05,
        "runtime_ms": 0.25,
        "scenario_feasible": True,
        "failure_category": "pass",
        "oracle_collision": False,
        "oracle_unsafe_gap": False,
        "oracle_minimum_gap": 12.0,
    }

    database.save_results(
        [
            result
        ],
        "test_run_001",
        "test_v1",
    )

    assert temporary_database.exists()

    connection = sqlite3.connect(
        temporary_database
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            run_id,
            model_version,
            scenario_id,
            status,
            scenario_feasible,
            failure_category
        FROM simulation_runs
        WHERE scenario_id = ?
        """,
        (
            "test_001",
        ),
    )

    row = cursor.fetchone()

    connection.close()

    assert row is not None

    assert (
        row[0]
        ==
        "test_run_001"
    )

    assert (
        row[1]
        ==
        "test_v1"
    )

    assert (
        row[2]
        ==
        "test_001"
    )

    assert (
        row[3]
        ==
        "PASS"
    )

    assert row[4] == 1

    assert (
        row[5]
        ==
        "pass"
    )