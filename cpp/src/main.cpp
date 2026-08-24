#include <exception>
#include <iomanip>
#include <iostream>
#include <string>

#include <nlohmann/json.hpp>

#include "simulation_runner.hpp"

using json = nlohmann::json;

int main(
    int argc,
    char* argv[]
) {
    if (
        argc
        !=
        2
    ) {
        std::cerr
            << "Usage: simulation_runner <scenario.json>\n";

        return 1;
    }

    try {
        const std::string scenarioPath =
            argv[1];

        const SimulationResult result =
            runSimulation(
                scenarioPath
            );

        json output;

        output[
            "scenario_id"
        ] =
            result.scenarioId;

        output[
            "status"
        ] =
            result.passed
            ?
            "PASS"
            :
            "FAIL";

        output[
            "collision"
        ] =
            result.collision;

        output[
            "unsafe_gap"
        ] =
            result.unsafeGap;

        output[
            "minimum_gap"
        ] =
            result.minimumGap;

        output[
            "minimum_ttc"
        ] =
            result.minimumTtc;

        output[
            "maximum_deceleration"
        ] =
            result.maximumDeceleration;

        output[
            "final_gap_error"
        ] =
            result.finalGapError;

        output[
            "final_relative_velocity"
        ] =
            result.finalRelativeVelocity;

        output[
            "runtime_ms"
        ] =
            result.runtimeMs;

        std::cout
            << std::fixed
            << std::setprecision(10)
            << output.dump()
            << '\n';

        return 0;
    }
    catch (
        const std::exception& error
    ) {
        json output;

        output[
            "status"
        ] =
            "ERROR";

        output[
            "error"
        ] =
            error.what();

        std::cerr
            << output.dump()
            << '\n';

        return 1;
    }
}