import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXECUTABLE_NAME = (
    "simulation_runner.exe"
    if os.name == "nt"
    else "simulation_runner"
)

EXECUTABLE = (
    ROOT
    / "build"
    / EXECUTABLE_NAME
)


def run_scenario(
    scenario_path,
):
    scenario_path = Path(
        scenario_path
    )

    if not EXECUTABLE.exists():
        return {
            "scenario_id": scenario_path.stem,
            "status": "ERROR",
            "error": (
                "Simulation executable not found: "
                f"{EXECUTABLE}"
            ),
        }

    process = subprocess.run(
        [
            str(EXECUTABLE),
            str(scenario_path),
        ],
        capture_output=True,
        text=True,
    )

    if process.returncode != 0:
        return {
            "scenario_id": scenario_path.stem,
            "status": "ERROR",
            "error": (
                process.stderr.strip()
                or
                process.stdout.strip()
                or
                "Simulation runner failed."
            ),
        }

    try:
        output = json.loads(
            process.stdout.strip()
        )

    except json.JSONDecodeError:
        return {
            "scenario_id": scenario_path.stem,
            "status": "ERROR",
            "error": (
                "Invalid JSON returned "
                "by simulation runner."
            ),
        }

    return output