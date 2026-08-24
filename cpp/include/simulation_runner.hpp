#pragma once

#include <string>

struct SimulationResult {
    std::string scenarioId;
    bool passed;
    bool collision;
    bool unsafeGap;
    double minimumGap;
    double minimumTtc;
    double maximumDeceleration;
    double finalGapError;
    double finalRelativeVelocity;
    double runtimeMs;
};

SimulationResult runSimulation(
    const std::string& scenarioPath
);