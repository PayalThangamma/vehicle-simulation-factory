#include "simulation_runner.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <limits>
#include <stdexcept>

#include <nlohmann/json.hpp>

#include "vehicle_model.hpp"

using json = nlohmann::json;

SimulationResult runSimulation(
    const std::string& scenarioPath
) {
    const auto startTime =
        std::chrono::steady_clock::now();

    std::ifstream input(
        scenarioPath
    );

    if (!input.is_open()) {
        throw std::runtime_error(
            "Could not open scenario file: "
            +
            scenarioPath
        );
    }

    json scenario;
    input >> scenario;

    const std::string scenarioId =
        scenario.at(
            "scenario_id"
        ).get<std::string>();

    const double egoInitialPosition =
        scenario.at(
            "ego_initial_position"
        ).get<double>();

    const double egoInitialVelocity =
        scenario.at(
            "ego_initial_velocity"
        ).get<double>();

    const double leadInitialPosition =
        scenario.at(
            "lead_initial_position"
        ).get<double>();

    const double leadInitialVelocity =
        scenario.at(
            "lead_initial_velocity"
        ).get<double>();

    const double desiredTimeHeadway =
        scenario.at(
            "desired_time_headway"
        ).get<double>();

    const double minimumGap =
        scenario.at(
            "minimum_gap"
        ).get<double>();

    const double gapKp =
        scenario.at(
            "gap_kp"
        ).get<double>();

    const double relativeVelocityKp =
        scenario.at(
            "relative_velocity_kp"
        ).get<double>();

    const double closingSpeedGain =
        scenario.at(
            "closing_speed_gain"
        ).get<double>();

    const double minimumAcceleration =
        scenario.at(
            "minimum_acceleration"
        ).get<double>();

    const double maximumAcceleration =
        scenario.at(
            "maximum_acceleration"
        ).get<double>();

    const double leadBrakeStart =
        scenario.at(
            "lead_brake_start"
        ).get<double>();

    const double leadBrakeDuration =
        scenario.at(
            "lead_brake_duration"
        ).get<double>();

    const double leadBrakeEnd =
        leadBrakeStart
        +
        leadBrakeDuration;

    const double leadBrakeAcceleration =
        scenario.at(
            "lead_brake_acceleration"
        ).get<double>();

    const double duration =
        scenario.at(
            "duration"
        ).get<double>();

    const double dt =
        scenario.at(
            "dt"
        ).get<double>();

    VehicleModel egoVehicle(
        egoInitialPosition,
        egoInitialVelocity
    );

    VehicleModel leadVehicle(
        leadInitialPosition,
        leadInitialVelocity
    );

    const int numberOfSteps =
        static_cast<int>(
            std::round(
                duration
                /
                dt
            )
        );

    double minimumObservedGap =
        leadInitialPosition
        -
        egoInitialPosition;

    double minimumObservedTtc =
        std::numeric_limits<double>::infinity();

    double maximumObservedDeceleration =
        0.0;

    bool collision = false;
    bool unsafeGap = false;

    for (
        int step = 0;
        step < numberOfSteps;
        ++step
    ) {
        const double time =
            static_cast<double>(
                step
            )
            *
            dt;

        const VehicleState egoState =
            egoVehicle.getState();

        const VehicleState leadState =
            leadVehicle.getState();

        const double gap =
            leadState.position
            -
            egoState.position;

        const double desiredGap =
            minimumGap
            +
            desiredTimeHeadway
            *
            egoState.velocity;

        const double gapError =
            gap
            -
            desiredGap;

        const double relativeVelocity =
            leadState.velocity
            -
            egoState.velocity;

        const double controllerClosingSpeed =
            std::max(
                egoState.velocity
                -
                leadState.velocity,
                0.0
            );

        const double rawAcceleration =
            gapKp
            *
            gapError
            +
            relativeVelocityKp
            *
            relativeVelocity
            -
            closingSpeedGain
            *
            controllerClosingSpeed;

        double commandedAcceleration =
            std::clamp(
                rawAcceleration,
                minimumAcceleration,
                maximumAcceleration
            );

        const double safetyClosingSpeed =
            egoState.velocity
            -
            leadState.velocity;

        if (
            safetyClosingSpeed > 0.0
            &&
            gap > 0.0
        ) {
            const double safetyTtc =
                gap
                /
                safetyClosingSpeed;

            if (
                safetyTtc < 1.5
            ) {
                commandedAcceleration =
                    minimumAcceleration;
            }
        }

        double leadAcceleration =
            0.0;

        if (
            time >= leadBrakeStart
            &&
            time < leadBrakeEnd
        ) {
            leadAcceleration =
                leadBrakeAcceleration;
        }

        if (
            commandedAcceleration
            <
            maximumObservedDeceleration
        ) {
            maximumObservedDeceleration =
                commandedAcceleration;
        }

        if (
            gap
            <
            minimumObservedGap
        ) {
            minimumObservedGap =
                gap;
        }

        if (
            gap <= 0.0
        ) {
            collision = true;
        }

        if (
            gap
            <
            minimumGap
        ) {
            unsafeGap = true;
        }

        const double closingSpeed =
            egoState.velocity
            -
            leadState.velocity;

        if (
            closingSpeed > 0.0
            &&
            gap > 0.0
        ) {
            const double ttc =
                gap
                /
                closingSpeed;

            if (
                ttc
                <
                minimumObservedTtc
            ) {
                minimumObservedTtc =
                    ttc;
            }
        }

        egoVehicle.stepRK4(
            commandedAcceleration,
            dt
        );

        leadVehicle.stepRK4(
            leadAcceleration,
            dt
        );
    }

    const VehicleState finalEgoState =
        egoVehicle.getState();

    const VehicleState finalLeadState =
        leadVehicle.getState();

    const double finalGap =
        finalLeadState.position
        -
        finalEgoState.position;

    const double finalDesiredGap =
        minimumGap
        +
        desiredTimeHeadway
        *
        finalEgoState.velocity;

    const double finalGapError =
        finalGap
        -
        finalDesiredGap;

    const double finalRelativeVelocity =
        finalLeadState.velocity
        -
        finalEgoState.velocity;

    if (
        !std::isfinite(
            minimumObservedTtc
        )
    ) {
        minimumObservedTtc =
            -1.0;
    }

    const bool convergencePassed =
        std::abs(
            finalGapError
        )
        <= 5.0
        &&
        std::abs(
            finalRelativeVelocity
        )
        <= 0.5;

    const bool passed =
        !collision
        &&
        !unsafeGap
        &&
        convergencePassed;

    const auto endTime =
        std::chrono::steady_clock::now();

    const double runtimeMs =
        std::chrono::duration<
            double,
            std::milli
        >(
            endTime
            -
            startTime
        ).count();

    SimulationResult result;

    result.scenarioId =
        scenarioId;

    result.passed =
        passed;

    result.collision =
        collision;

    result.unsafeGap =
        unsafeGap;

    result.minimumGap =
        minimumObservedGap;

    result.minimumTtc =
        minimumObservedTtc;

    result.maximumDeceleration =
        maximumObservedDeceleration;

    result.finalGapError =
        finalGapError;

    result.finalRelativeVelocity =
        finalRelativeVelocity;

    result.runtimeMs =
        runtimeMs;

    return result;
}