import sqlite3
from datetime import datetime
from datetime import timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    ROOT
    / "results"
    / "simulation_factory.db"
)


def get_connection():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return sqlite3.connect(
        DATABASE_PATH
    )


def add_column_if_missing(
    connection,
    column_name,
    column_definition,
):
    cursor = connection.cursor()

    cursor.execute(
        """
        PRAGMA table_info(simulation_runs)
        """
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if column_name not in existing_columns:
        cursor.execute(
            f"""
            ALTER TABLE simulation_runs
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


def initialize_database():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS simulation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            scenario_id TEXT NOT NULL,
            status TEXT NOT NULL,
            failure_reason TEXT,
            collision INTEGER NOT NULL,
            unsafe_gap INTEGER NOT NULL,
            minimum_gap REAL,
            minimum_ttc REAL,
            maximum_deceleration REAL,
            final_gap_error REAL,
            final_relative_velocity REAL,
            runtime_ms REAL,
            created_at TEXT NOT NULL
        )
        """
    )

    add_column_if_missing(
        connection,
        "scenario_feasible",
        "INTEGER",
    )

    add_column_if_missing(
        connection,
        "failure_category",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "oracle_collision",
        "INTEGER",
    )

    add_column_if_missing(
        connection,
        "oracle_unsafe_gap",
        "INTEGER",
    )

    add_column_if_missing(
        connection,
        "oracle_minimum_gap",
        "REAL",
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_simulation_runs_run_id
        ON simulation_runs(run_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_simulation_runs_scenario_id
        ON simulation_runs(scenario_id)
        """
    )

    connection.commit()
    connection.close()


def save_results(
    results,
    run_id,
    model_version,
):
    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    for result in results:
        cursor.execute(
            """
            INSERT INTO simulation_runs (
                run_id,
                model_version,
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
                runtime_ms,
                created_at,
                scenario_feasible,
                failure_category,
                oracle_collision,
                oracle_unsafe_gap,
                oracle_minimum_gap
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                run_id,
                model_version,
                result.get(
                    "scenario_id"
                ),
                result.get(
                    "status"
                ),
                result.get(
                    "failure_reason"
                ),
                int(
                    result.get(
                        "collision",
                        False,
                    )
                ),
                int(
                    result.get(
                        "unsafe_gap",
                        False,
                    )
                ),
                result.get(
                    "minimum_gap"
                ),
                result.get(
                    "minimum_ttc"
                ),
                result.get(
                    "maximum_deceleration"
                ),
                result.get(
                    "final_gap_error"
                ),
                result.get(
                    "final_relative_velocity"
                ),
                result.get(
                    "runtime_ms"
                ),
                timestamp,
                (
                    int(
                        result[
                            "scenario_feasible"
                        ]
                    )
                    if result.get(
                        "scenario_feasible"
                    )
                    is not None
                    else None
                ),
                result.get(
                    "failure_category"
                ),
                (
                    int(
                        result[
                            "oracle_collision"
                        ]
                    )
                    if result.get(
                        "oracle_collision"
                    )
                    is not None
                    else None
                ),
                (
                    int(
                        result[
                            "oracle_unsafe_gap"
                        ]
                    )
                    if result.get(
                        "oracle_unsafe_gap"
                    )
                    is not None
                    else None
                ),
                result.get(
                    "oracle_minimum_gap"
                ),
            ),
        )

    connection.commit()
    connection.close()


def generate_run_id():
    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT run_id
        FROM simulation_runs
        """
    )

    run_numbers = []

    for row in cursor.fetchall():
        run_id = row[0]

        if (
            run_id
            and
            run_id.startswith(
                "run_"
            )
        ):
            try:
                run_numbers.append(
                    int(
                        run_id.split(
                            "_"
                        )[1]
                    )
                )
            except ValueError:
                pass

    connection.close()

    next_number = (
        max(
            run_numbers,
            default=0,
        )
        +
        1
    )

    return (
        f"run_{next_number:03d}"
    )