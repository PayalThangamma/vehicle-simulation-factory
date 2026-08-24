import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASE_SCENARIO_PATH = (
    ROOT
    / "scenarios"
    / "base_scenario.json"
)

OUTPUT_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)


def load_base_scenario():
    with open(
        BASE_SCENARIO_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def generate_scenario(
    base,
    index,
):
    scenario = dict(
        base
    )

    scenario[
        "scenario_id"
    ] = (
        f"acc_{index:05d}"
    )

    ego_velocity = random.uniform(
        8.0,
        30.0,
    )

    lead_velocity = random.uniform(
        8.0,
        30.0,
    )

    initial_gap = random.uniform(
        10.0,
        60.0,
    )

    scenario[
    "closing_speed_gain"
] = round(
    random.uniform(
        0.2,
        0.6,
    ),
    6,
)

    scenario[
        "ego_initial_position"
    ] = 0.0

    scenario[
        "ego_initial_velocity"
    ] = round(
        ego_velocity,
        6,
    )

    scenario[
        "lead_initial_position"
    ] = round(
        initial_gap,
        6,
    )

    scenario[
        "lead_initial_velocity"
    ] = round(
        lead_velocity,
        6,
    )

    scenario[
        "desired_time_headway"
    ] = round(
        random.uniform(
            1.0,
            2.5,
        ),
        6,
    )

    scenario[
        "minimum_gap"
    ] = round(
        random.uniform(
            3.0,
            8.0,
        ),
        6,
    )

    scenario[
        "gap_kp"
    ] = round(
        random.uniform(
            0.2,
            0.6,
        ),
        6,
    )

    scenario[
        "relative_velocity_kp"
    ] = round(
        random.uniform(
            0.5,
            1.2,
        ),
        6,
    )

    scenario[
        "lead_brake_start"
    ] = round(
        random.uniform(
            2.0,
            8.0,
        ),
        6,
    )

    scenario[
        "lead_brake_duration"
    ] = round(
        random.uniform(
            0.5,
            3.0,
        ),
        6,
    )

    scenario[
        "lead_brake_acceleration"
    ] = round(
        random.uniform(
            -6.0,
            -1.0,
        ),
        6,
    )

    return scenario


def generate_scenarios(
    count,
    seed,
):
    random.seed(
        seed
    )

    base = load_base_scenario()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_files = list(
        OUTPUT_DIR.glob(
            "*.json"
        )
    )

    for path in existing_files:
        path.unlink()

    for index in range(
        1,
        count + 1,
    ):
        scenario = generate_scenario(
            base,
            index,
        )

        output_path = (
            OUTPUT_DIR
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

    print(
        "============================================"
    )

    print(
        "Scenario Generation Complete"
    )

    print(
        "============================================"
    )

    print(
        f"Generated scenarios: {count}"
    )

    print(
        f"Random seed:        {seed}"
    )

    print(
        f"Output directory:   {OUTPUT_DIR}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--count",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if args.count <= 0:
        raise ValueError(
            "Scenario count must be greater than zero."
        )

    generate_scenarios(
        args.count,
        args.seed,
    )


if __name__ == "__main__":
    main()