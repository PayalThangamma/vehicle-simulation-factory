import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)


def integrate_vehicle(
    position,
    velocity,
    acceleration,
    dt,
):
    if (
        velocity <= 0.0
        and
        acceleration < 0.0
    ):
        return position, 0.0

    next_velocity = (
        velocity
        +
        acceleration
        *
        dt
    )

    if next_velocity < 0.0:
        if acceleration == 0.0:
            return position, 0.0

        stop_time = (
            -velocity
            /
            acceleration
        )

        stop_time = max(
            0.0,
            min(
                stop_time,
                dt,
            ),
        )

        next_position = (
            position
            +
            velocity
            *
            stop_time
            +
            0.5
            *
            acceleration
            *
            stop_time
            *
            stop_time
        )

        return (
            next_position,
            0.0,
        )

    next_position = (
        position
        +
        velocity
        *
        dt
        +
        0.5
        *
        acceleration
        *
        dt
        *
        dt
    )

    return (
        next_position,
        next_velocity,
    )


def evaluate_scenario(
    scenario,
):
    ego_position = scenario[
        "ego_initial_position"
    ]

    ego_velocity = scenario[
        "ego_initial_velocity"
    ]

    lead_position = scenario[
        "lead_initial_position"
    ]

    lead_velocity = scenario[
        "lead_initial_velocity"
    ]

    ego_braking = scenario[
        "minimum_acceleration"
    ]

    lead_braking = scenario[
        "lead_brake_acceleration"
    ]

    lead_brake_start = scenario[
        "lead_brake_start"
    ]

    lead_brake_end = (
        lead_brake_start
        +
        scenario[
            "lead_brake_duration"
        ]
    )

    minimum_gap = scenario[
        "minimum_gap"
    ]

    duration = scenario[
        "duration"
    ]

    dt = scenario[
        "dt"
    ]

    number_of_steps = round(
        duration
        /
        dt
    )

    minimum_observed_gap = (
        lead_position
        -
        ego_position
    )

    collision = False
    unsafe_gap = False

    for step in range(
        number_of_steps
    ):
        time = (
            step
            *
            dt
        )

        gap = (
            lead_position
            -
            ego_position
        )

        minimum_observed_gap = min(
            minimum_observed_gap,
            gap,
        )

        if gap < minimum_gap:
            unsafe_gap = True

        if gap <= 0.0:
            collision = True

        lead_acceleration = 0.0

        if (
            time >= lead_brake_start
            and
            time < lead_brake_end
        ):
            lead_acceleration = (
                lead_braking
            )

        ego_position, ego_velocity = (
            integrate_vehicle(
                ego_position,
                ego_velocity,
                ego_braking,
                dt,
            )
        )

        lead_position, lead_velocity = (
            integrate_vehicle(
                lead_position,
                lead_velocity,
                lead_acceleration,
                dt,
            )
        )

    final_gap = (
        lead_position
        -
        ego_position
    )

    minimum_observed_gap = min(
        minimum_observed_gap,
        final_gap,
    )

    if final_gap < minimum_gap:
        unsafe_gap = True

    if final_gap <= 0.0:
        collision = True

    feasible = (
        not unsafe_gap
        and
        not collision
    )

    return {
        "feasible": feasible,
        "oracle_collision": collision,
        "oracle_unsafe_gap": unsafe_gap,
        "oracle_minimum_gap": minimum_observed_gap,
    }


def evaluate_scenario_file(
    scenario_path,
):
    with open(
        scenario_path,
        "r",
        encoding="utf-8",
    ) as file:
        scenario = json.load(
            file
        )

    return evaluate_scenario(
        scenario
    )