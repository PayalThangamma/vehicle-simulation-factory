import sqlite3

from factory.database import DATABASE_PATH


def main():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            scenario_id,
            failure_reason,
            collision,
            unsafe_gap,
            minimum_gap,
            minimum_ttc,
            maximum_deceleration,
            final_gap_error,
            final_relative_velocity
        FROM simulation_runs
        WHERE run_id = ?
        ORDER BY scenario_id
        """,
        (
            "run_004",
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    print()
    print(
        "============================================"
    )
    print(
        "Failure Analysis - run_004"
    )
    print(
        "============================================"
    )

    for row in rows:
        (
            scenario_id,
            failure_reason,
            collision,
            unsafe_gap,
            minimum_gap,
            minimum_ttc,
            maximum_deceleration,
            final_gap_error,
            final_relative_velocity,
        ) = row

        print()
        print(
            f"Scenario:               {scenario_id}"
        )

        print(
            f"Failure reason:          {failure_reason}"
        )

        print(
            f"Collision:               {bool(collision)}"
        )

        print(
            f"Unsafe gap:              {bool(unsafe_gap)}"
        )

        print(
            f"Minimum gap:             {minimum_gap:.4f} m"
        )

        print(
            f"Minimum TTC:             {minimum_ttc:.4f} s"
        )

        print(
            f"Maximum deceleration:    {maximum_deceleration:.4f} m/s^2"
        )

        print(
            f"Final gap error:         {final_gap_error:.4f} m"
        )

        print(
            f"Final relative velocity: {final_relative_velocity:.4f} m/s"
        )

        print(
            "--------------------------------------------"
        )


if __name__ == "__main__":
    main()