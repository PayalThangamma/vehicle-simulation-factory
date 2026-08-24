import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SCENARIO_DIR = (
    ROOT
    / "scenarios"
    / "generated"
)

FAILED_SCENARIOS = [
    "acc_00001",
    "acc_00005",
    "acc_00008",
    "acc_00010",
    "acc_00014",
    "acc_00030",
    "acc_00032",
    "acc_00035",
    "acc_00056",
    "acc_00059",
    "acc_00060",
    "acc_00073",
    "acc_00086",
    "acc_00093",
    "acc_00099",
]


def integrate_vehicle(
    position,
    velocity,
    acceleration,
    dt,
):
    if velocity <= 0.0 and acceleration < 0.0:
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

    first_unsafe_time = None
    first_collision_time = None

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

        if (
            gap
            <
            minimum_gap
            and
            first_unsafe_time
            is None
        ):
            unsafe_gap = True

            first_unsafe_time = time

        if (
            gap
            <=
            0.0
            and
            first_collision_time
            is None
        ):
            collision = True

            first_collision_time = time

        lead_acceleration = 0.0

        if (
            time
            >=
            lead_brake_start
            and
            time
            <
            lead_brake_end
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

    if (
        final_gap
        <
        minimum_gap
        and
        first_unsafe_time
        is None
    ):
        unsafe_gap = True

        first_unsafe_time = duration

    if (
        final_gap
        <=
        0.0
        and
        first_collision_time
        is None
    ):
        collision = True

        first_collision_time = duration

    feasible = (
        not collision
        and
        not unsafe_gap
    )

    return {
        "feasible": feasible,
        "collision": collision,
        "unsafe_gap": unsafe_gap,
        "minimum_gap": minimum_observed_gap,
        "first_unsafe_time": first_unsafe_time,
        "first_collision_time": first_collision_time,
    }


def main():
    feasible = []
    infeasible = []

    print()
    print(
        "============================================"
    )
    print(
        "Maximum-Braking Feasibility Oracle"
    )
    print(
        "============================================"
    )

    for scenario_id in FAILED_SCENARIOS:
        scenario_path = (
            SCENARIO_DIR
            /
            f"{scenario_id}.json"
        )

        if not scenario_path.exists():
            print(
                f"{scenario_id}: file missing"
            )
            continue

        with open(
            scenario_path,
            "r",
            encoding="utf-8",
        ) as file:
            scenario = json.load(
                file
            )

        result = evaluate_scenario(
            scenario
        )

        if result[
            "feasible"
        ]:
            feasible.append(
                scenario_id
            )
        else:
            infeasible.append(
                scenario_id
            )

        print()
        print(
            f"Scenario:             {scenario_id}"
        )

        print(
            f"Oracle feasible:      {result['feasible']}"
        )

        print(
            f"Unsafe gap:           {result['unsafe_gap']}"
        )

        print(
            f"Collision:            {result['collision']}"
        )

        print(
            "Minimum oracle gap:   "
            f"{result['minimum_gap']:.4f} m"
        )

        if (
            result[
                "first_unsafe_time"
            ]
            is not None
        ):
            print(
                "First unsafe time:    "
                f"{result['first_unsafe_time']:.3f} s"
            )

        if (
            result[
                "first_collision_time"
            ]
            is not None
        ):
            print(
                "First collision time: "
                f"{result['first_collision_time']:.3f} s"
            )

        print(
            "--------------------------------------------"
        )

    print()
    print(
        "============================================"
    )
    print(
        "Oracle Summary"
    )
    print(
        "============================================"
    )

    print(
        f"Feasible:             {len(feasible)}"
    )

    print(
        f"Infeasible:           {len(infeasible)}"
    )

    print()

    print(
        "Feasible scenarios:"
    )

    for scenario_id in feasible:
        print(
            f"  {scenario_id}"
        )

    print()

    print(
        "Infeasible scenarios:"
    )

    for scenario_id in infeasible:
        print(
            f"  {scenario_id}"
        )

    print(
        "============================================"
    )


if __name__ == "__main__":
    main()