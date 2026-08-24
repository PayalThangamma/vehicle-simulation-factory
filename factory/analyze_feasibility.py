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


def stopping_distance(
    velocity,
    deceleration,
):
    deceleration = abs(
        deceleration
    )

    if deceleration <= 0.0:
        return float("inf")

    return (
        velocity
        *
        velocity
        /
        (
            2.0
            *
            deceleration
        )
    )


def analyze_scenario(
    scenario_id,
):
    path = (
        SCENARIO_DIR
        /
        f"{scenario_id}.json"
    )

    if not path.exists():
        print(
            f"{scenario_id}: scenario file missing"
        )
        return

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        scenario = json.load(
            file
        )

    ego_velocity = scenario[
        "ego_initial_velocity"
    ]

    lead_velocity = scenario[
        "lead_initial_velocity"
    ]

    ego_position = scenario[
        "ego_initial_position"
    ]

    lead_position = scenario[
        "lead_initial_position"
    ]

    minimum_acceleration = scenario[
        "minimum_acceleration"
    ]

    lead_brake_acceleration = scenario[
        "lead_brake_acceleration"
    ]

    minimum_gap = scenario[
        "minimum_gap"
    ]

    initial_gap = (
        lead_position
        -
        ego_position
    )

    relative_velocity = (
        ego_velocity
        -
        lead_velocity
    )

    ego_stop_distance = stopping_distance(
        ego_velocity,
        minimum_acceleration,
    )

    lead_stop_distance = stopping_distance(
        lead_velocity,
        lead_brake_acceleration,
    )

    relative_stop_requirement = (
        ego_stop_distance
        -
        lead_stop_distance
    )

    required_gap = max(
        minimum_gap,
        relative_stop_requirement
        +
        minimum_gap,
    )

    safety_margin = (
        initial_gap
        -
        required_gap
    )

    initially_closing = (
        relative_velocity
        >
        0.0
    )

    feasible = (
        safety_margin
        >=
        0.0
    )

    print()
    print(
        "============================================"
    )

    print(
        f"Scenario:               {scenario_id}"
    )

    print(
        "--------------------------------------------"
    )

    print(
        f"Ego velocity:            {ego_velocity:.3f} m/s"
    )

    print(
        f"Lead velocity:           {lead_velocity:.3f} m/s"
    )

    print(
        f"Relative closing speed:  {relative_velocity:.3f} m/s"
    )

    print(
        f"Initial gap:             {initial_gap:.3f} m"
    )

    print(
        f"Minimum allowed gap:     {minimum_gap:.3f} m"
    )

    print()

    print(
        f"Ego stopping distance:   {ego_stop_distance:.3f} m"
    )

    print(
        f"Lead stopping distance:  {lead_stop_distance:.3f} m"
    )

    print(
        f"Required gap estimate:   {required_gap:.3f} m"
    )

    print(
        f"Safety margin:           {safety_margin:.3f} m"
    )

    print()

    print(
        f"Initially closing:       {initially_closing}"
    )

    print(
        f"Estimated feasible:      {feasible}"
    )


def main():
    print()
    print(
        "============================================"
    )
    print(
        "Failed Scenario Feasibility Analysis"
    )
    print(
        "============================================"
    )

    feasible_count = 0
    infeasible_count = 0

    for scenario_id in FAILED_SCENARIOS:
        path = (
            SCENARIO_DIR
            /
            f"{scenario_id}.json"
        )

        if not path.exists():
            continue

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            scenario = json.load(
                file
            )

        ego_velocity = scenario[
            "ego_initial_velocity"
        ]

        lead_velocity = scenario[
            "lead_initial_velocity"
        ]

        initial_gap = (
            scenario[
                "lead_initial_position"
            ]
            -
            scenario[
                "ego_initial_position"
            ]
        )

        minimum_gap = scenario[
            "minimum_gap"
        ]

        ego_stop_distance = stopping_distance(
            ego_velocity,
            scenario[
                "minimum_acceleration"
            ],
        )

        lead_stop_distance = stopping_distance(
            lead_velocity,
            scenario[
                "lead_brake_acceleration"
            ],
        )

        required_gap = max(
            minimum_gap,
            ego_stop_distance
            -
            lead_stop_distance
            +
            minimum_gap,
        )

        feasible = (
            initial_gap
            >=
            required_gap
        )

        if feasible:
            feasible_count += 1
        else:
            infeasible_count += 1

        analyze_scenario(
            scenario_id
        )

    print()
    print(
        "============================================"
    )
    print(
        "Summary"
    )
    print(
        "============================================"
    )

    print(
        f"Feasible scenarios:       {feasible_count}"
    )

    print(
        f"Potentially infeasible:   {infeasible_count}"
    )

    print(
        "============================================"
    )


if __name__ == "__main__":
    main()