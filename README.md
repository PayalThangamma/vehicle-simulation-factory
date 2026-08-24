# Distributed Vehicle Simulation Factory

A production-style vehicle simulation pipeline for running, validating, reprocessing, and analyzing large batches of Adaptive Cruise Control simulations.

The project combines a C++ simulation engine with Python orchestration, multiprocessing, failure classification, feasibility analysis, SQLite experiment tracking, automated testing, Docker, CI, and performance benchmarking.

---

## Overview

This project implements a small-scale simulation factory for longitudinal vehicle and Adaptive Cruise Control experiments.

The system can:

- generate reproducible simulation scenarios
- execute simulations through a compiled C++ engine
- distribute simulations across multiple worker processes
- collect safety and convergence metrics
- classify failures
- distinguish model failures from physically infeasible scenarios
- reprocess failed scenarios
- compare model versions
- track experiment history in SQLite
- benchmark multiprocessing scalability
- generate analysis plots
- run automated tests
- execute reproducibly in Docker
- validate automatically through GitHub Actions

The goal is not only to simulate vehicle behavior, but to build the surrounding infrastructure required to operate a repeatable simulation workflow.

---

# Architecture

```text
Base Scenario
      |
      v
Scenario Generator
      |
      v
Generated JSON Scenarios
      |
      v
Python Simulation Factory
      |
      +-------------------------------+
      |               |               |
      v               v               v
   Worker 1         Worker 2        Worker N
      |               |               |
      +---------------+---------------+
                      |
                      v
              C++ Simulation Runner
                      |
                      v
             Vehicle + ACC Dynamics
                      |
                      v
                Run Metrics
                      |
          +-----------+-----------+
          |                       |
          v                       v
       SQLite                 JSON Results
          |                       |
          +-----------+-----------+
                      |
                      v
           Failure Classification
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Feasibility Oracle        Model Failure
          |                       |
          +-----------+-----------+
                      |
                      v
             Analysis + Reports
````

---

# Technology Stack

## Simulation

* C++17
* CMake
* Ninja
* nlohmann/json
* Runge-Kutta 4 numerical integration

## Simulation Factory

* Python 3.12
* `ProcessPoolExecutor`
* SQLite
* JSON scenario configuration
* deterministic scenario generation

## Analysis

* matplotlib
* CSV benchmark reports
* safety metric visualization
* scalability analysis

## Engineering

* pytest
* Docker
* GitHub Actions
* Windows and Linux support

---

# Vehicle Model

The simulation uses a longitudinal vehicle model:

```text
dx/dt = v
dv/dt = a
```

where:

* `x` is vehicle position
* `v` is vehicle velocity
* `a` is commanded acceleration

Vehicle state integration is performed using RK4.

Each simulation includes:

* ego vehicle
* lead vehicle
* Adaptive Cruise Control controller
* configurable lead-vehicle braking event
* acceleration saturation
* minimum-gap monitoring
* time-to-collision monitoring
* convergence evaluation

---

# Adaptive Cruise Control

The ACC controller combines:

* gap error
* relative velocity
* closing-speed feedback

The control law is:

```text
a_cmd =
    K_gap * gap_error
    + K_rel * relative_velocity
    - K_close * closing_speed
```

with:

```text
gap_error =
    actual_gap
    -
    desired_gap
```

and:

```text
desired_gap =
    minimum_gap
    +
    time_headway * ego_velocity
```

The commanded acceleration is then constrained by configurable minimum and maximum acceleration limits.

The current model also contains a TTC-based safety supervisor that can request maximum braking when estimated time-to-collision becomes critically low.

---

# Scenario Generation

Simulation scenarios are stored as JSON.

The generator varies:

* ego initial velocity
* lead initial velocity
* initial vehicle gap
* desired time headway
* minimum safety gap
* gap controller gain
* relative-velocity gain
* closing-speed gain
* lead braking start time
* lead braking duration
* lead braking acceleration

Scenario generation uses a fixed random seed so experiments can be reproduced.

Example:

```bash
python -m factory.generate_scenarios --count 100 --seed 42
```

---

# Example Scenario

```json
{
  "scenario_id": "acc_00001",
  "ego_initial_position": 0.0,
  "ego_initial_velocity": 22.06739,
  "lead_initial_position": 23.751466,
  "lead_initial_velocity": 8.550237,
  "desired_time_headway": 1.334816,
  "minimum_gap": 6.682356,
  "gap_kp": 0.47068,
  "relative_velocity_kp": 1.124526,
  "closing_speed_gain": 0.4,
  "minimum_acceleration": -5.0,
  "maximum_acceleration": 3.0,
  "lead_brake_start": 2.521633,
  "lead_brake_duration": 1.554805,
  "lead_brake_acceleration": -5.851014,
  "duration": 15.0,
  "dt": 0.01
}
```

---

# Simulation Factory

Run the complete scenario set:

```bash
python -m factory.run_factory \
    --workers 4 \
    --model-version v3 \
    --duration 30
```

The factory performs the following workflow:

```text
Load scenarios
      |
      v
Evaluate physical feasibility
      |
      v
Create worker pool
      |
      v
Execute C++ simulations
      |
      v
Collect simulation metrics
      |
      v
Classify outcomes
      |
      v
Store experiment results
      |
      v
Generate machine-readable summary
```

---

# Simulation Metrics

Each simulation returns:

* scenario ID
* pass/fail status
* collision flag
* unsafe-gap flag
* minimum observed gap
* minimum TTC
* maximum deceleration
* final gap error
* final relative velocity
* simulation runtime

Example:

```json
{
  "scenario_id": "base_acc_001",
  "status": "PASS",
  "collision": false,
  "unsafe_gap": false,
  "minimum_gap": 23.2164,
  "minimum_ttc": 6.7747,
  "maximum_deceleration": -3.2119,
  "final_gap_error": 0.0975,
  "final_relative_velocity": -0.0787,
  "runtime_ms": 0.3425
}
```

---

# Failure Classification

Simulation results are classified into:

```text
PASS
MODEL_FAILURE
INFEASIBLE_SCENARIO
ERROR
```

Model failures are further classified into:

* collision
* unsafe gap
* gap convergence
* velocity convergence
* simulation error

This separation prevents every failed simulation from being incorrectly treated as a controller defect.

---

# Feasibility Oracle

A separate maximum-braking feasibility oracle evaluates whether a scenario is physically avoidable.

The oracle:

1. applies maximum ego braking from the beginning
2. reproduces the configured lead-vehicle braking event
3. propagates both vehicle states
4. checks minimum gap and collision conditions

A scenario is classified as physically infeasible when it still violates the minimum safety gap even under maximum ego braking.

This provides a useful separation between:

```text
controller failure
```

and:

```text
physically unavoidable scenario
```

---

# Validation Investigation

The original validation used a 15-second simulation horizon.

## Initial result

```text
Total scenarios: 100
Passed:          85
Failed:          15
```

The failed scenarios were analyzed individually.

The feasibility oracle determined:

```text
Feasible failed scenarios: 9
Infeasible scenarios:      6
```

The six infeasible scenarios were:

```text
acc_00001
acc_00005
acc_00032
acc_00035
acc_00060
acc_00086
```

These scenarios violated the required safety gap even when the ego vehicle applied maximum braking from the beginning of the simulation.

---

# Extended-Horizon Diagnostic

The nine remaining feasible failures were convergence-related.

They were rerun with a 30-second simulation horizon.

Result:

```text
Scenarios tested:          9
Converged:                 9
Gap convergence failures:  0
Velocity failures:         0
Errors:                    0
```

This showed that the controller was not unstable.

Instead, the original 15-second evaluation horizon was insufficient for some valid scenarios to satisfy the convergence criteria.

---

# Final Validation Result

A clean 100-scenario validation was then executed using a 30-second horizon.

```text
Total scenarios:          100
Passed:                   94
Model failures:           0
Infeasible scenarios:     6
Errors:                   0

Observed collisions:      4
Observed unsafe gaps:     6

Feasible gap failures:    0
Feasible velocity fails:  0

Feasible scenarios:       94
Feasible pass rate:       100.00%
```

## Final interpretation

```text
100 scenarios
│
├── 94 physically feasible
│   └── 94 passed
│
└── 6 physically infeasible
```

Therefore:

```text
Feasible validation pass rate = 100%
```

with zero genuine model failures in the validated feasible scenario set.

---

# Failed-Scenario Reprocessing

Failed scenarios can be selectively rerun.

Example:

```bash
python -m factory.reprocess_failed \
    --source-run run_004 \
    --model-version v3 \
    --workers 4
```

This allows the factory to re-evaluate only problematic scenarios instead of rerunning the entire dataset.

---

# Experiment Tracking

Experiments are stored in SQLite.

Each result contains:

* run ID
* model version
* scenario ID
* status
* failure reason
* feasibility classification
* collision state
* unsafe-gap state
* minimum gap
* minimum TTC
* maximum deceleration
* final gap error
* final relative velocity
* runtime
* timestamp

This makes experiments auditable and enables comparison between model versions.

---

# Run Comparison

Runs can be compared using:

```bash
python -m factory.summarize_results \
    --baseline run_004 \
    --candidate run_005
```

Comparison metrics include:

* improved scenarios
* regressed scenarios
* persistent failures
* failure-reason changes
* collisions
* unsafe gaps
* convergence quality
* runtime changes

Example output:

```text
Simulation Run Comparison

Baseline run:       run_004
Candidate run:      run_005
Common scenarios:   15

Improved scenarios: 0
Regressed scenarios:0
Persistent failures:15
```

This functionality supports regression testing across controller versions.

---

# Performance Scaling Benchmark

The factory was benchmarked across:

```text
100 scenarios
500 scenarios
1000 scenarios
5000 scenarios
```

using:

```text
1 worker
2 workers
4 workers
8 workers
```

## Benchmark Results

| Scenarios | Workers | Execution Time |  Throughput | Speedup | Efficiency |
| --------: | ------: | -------------: | ----------: | ------: | ---------: |
|       100 |       1 |        6.677 s | 14.98 sim/s |   1.00x |    100.00% |
|       100 |       2 |        4.505 s | 22.20 sim/s |   1.48x |     74.11% |
|       100 |       4 |        4.224 s | 23.68 sim/s |   1.58x |     39.52% |
|       100 |       8 |        4.979 s | 20.08 sim/s |   1.34x |     16.76% |
|       500 |       1 |       32.251 s | 15.50 sim/s |   1.00x |    100.00% |
|       500 |       2 |       21.295 s | 23.48 sim/s |   1.51x |     75.73% |
|       500 |       4 |       20.547 s | 24.33 sim/s |   1.57x |     39.24% |
|       500 |       8 |       20.741 s | 24.11 sim/s |   1.55x |     19.44% |
|      1000 |       1 |       64.350 s | 15.54 sim/s |   1.00x |    100.00% |
|      1000 |       2 |       50.045 s | 19.98 sim/s |   1.29x |     64.29% |
|      1000 |       4 |       40.889 s | 24.46 sim/s |   1.57x |     39.34% |
|      1000 |       8 |       41.317 s | 24.20 sim/s |   1.56x |     19.47% |
|      5000 |       1 |      327.503 s | 15.27 sim/s |   1.00x |    100.00% |
|      5000 |       2 |      224.504 s | 22.27 sim/s |   1.46x |     72.94% |
|      5000 |       4 |      213.140 s | 23.46 sim/s |   1.54x |     38.41% |
|      5000 |       8 |      210.091 s | 23.80 sim/s |   1.56x |     19.49% |

---

# Scaling Analysis

The benchmark demonstrates that additional worker processes improve throughput only up to a point.

Observed behavior:

```text
1 worker
    |
    v
~15 simulations/s

2 workers
    |
    v
~20-23 simulations/s

4 workers
    |
    v
~23-24 simulations/s

8 workers
    |
    v
~20-24 simulations/s
```

Key findings:

* two workers provide a clear improvement over serial execution
* four workers provide the best throughput for most workloads
* throughput saturates around 23-24 simulations per second
* eight workers provide little additional benefit
* for small workloads, eight workers can be slower
* process scheduling and orchestration overhead dominate once worker count becomes too high

The factory therefore demonstrates both the benefit and the limits of local multiprocessing.

---

# Performance Reports

Benchmark plots are generated automatically.

```text
results/reports/throughput_scaling.png
results/reports/parallel_speedup.png
results/reports/parallel_efficiency.png
```

Safety-analysis plots include:

```text
results/reports/run_007_outcomes.png
results/reports/run_007_minimum_gap_distribution.png
results/reports/run_007_ttc_vs_gap.png
results/reports/run_007_infeasible_scenarios.png
```

The raw scaling benchmark is stored at:

```text
results/reports/scaling_benchmark.csv
```

---

# Safety Analysis

Safety visualization includes:

* pass vs infeasible outcomes
* minimum-gap distribution
* TTC vs minimum-gap relationship
* individual infeasible scenarios
* collision boundary visualization

Example safety summary:

```text
Total scenarios:        100
Passed:                 94
Model failures:         0
Infeasible scenarios:   6
Collisions:             4
Unsafe gaps:            6
Feasible scenarios:     94
Feasible pass rate:     100.00%
```

---

# Automated Tests

The project includes 18 automated tests.

Coverage includes:

* pass classification
* collision classification
* unsafe-gap classification
* gap-convergence classification
* velocity-convergence classification
* simulation-error classification
* model-failure categorization
* infeasible-scenario categorization
* feasibility oracle behavior
* scenario-file existence
* scenario JSON structure
* validated feasibility counts
* simulation execution
* deterministic simulation output
* SQLite persistence

Run:

```bash
python -m pytest tests -v
```

Current result:

```text
18 passed
```

---

# Deterministic Simulation

The simulation runner is tested for reproducibility.

Running the same scenario repeatedly must produce the same:

* collision result
* unsafe-gap result
* minimum gap
* minimum TTC
* maximum deceleration
* final gap error
* final relative velocity

Runtime itself is excluded from deterministic comparison.

---

# Windows One-Command Pipeline

The project includes:

```text
run_factory.ps1
```

Run:

```powershell
.\run_factory.ps1
```

or:

```powershell
.\run_factory.ps1 `
  -Workers 4 `
  -Duration 30 `
  -ModelVersion v3
```

The pipeline automatically performs:

```text
CMake configuration
        |
        v
C++ build
        |
        v
pytest
        |
        v
100-scenario validation
        |
        v
SQLite + JSON results
        |
        v
performance plots
```

Example successful result:

```text
18 tests passed

Total scenarios:          100
Passed:                   94
Model failures:           0
Infeasible scenarios:     6
Feasible pass rate:       100.00%
```

---

# Docker

The full project can be built and executed inside Linux using Docker.

Build:

```bash
docker build -t vehicle-simulation-factory .
```

Run:

```bash
docker run --rm vehicle-simulation-factory
```

The Docker image:

1. installs C++ build dependencies
2. installs Python dependencies
3. configures CMake
4. builds the C++ simulator
5. runs the automated tests
6. executes the full simulation validation

Example Docker result:

```text
Total scenarios:          100
Passed:                   94
Model failures:           0
Infeasible scenarios:     6
Errors:                   0

Feasible pass rate:       100.00%
```

Docker is used as a portability and reproducibility check rather than as a direct performance comparison with the native Windows benchmark.

---

# Continuous Integration

GitHub Actions validates the project on Ubuntu.

The CI workflow performs:

```text
Checkout repository
        |
        v
Install Python dependencies
        |
        v
Configure CMake
        |
        v
Build C++ simulator
        |
        v
Run 18 automated tests
        |
        v
Run full 100-scenario validation
        |
        v
Build Docker image
        |
        v
Run Docker validation
```

CI runs automatically for:

* pushes to `main`
* pull requests targeting `main`

---

# CMake Build

Manual C++ build:

```bash
cmake \
    -S cpp \
    -B build \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release
```

Then:

```bash
cmake --build build
```

On Windows with MSYS2:

```powershell
C:\msys64\ucrt64\bin\cmake.exe `
  -S .\cpp `
  -B .\build `
  -G Ninja `
  -DCMAKE_CXX_COMPILER=C:/msys64/ucrt64/bin/g++.exe
```

Then:

```powershell
C:\msys64\ucrt64\bin\cmake.exe --build .\build
```

---

# Run a Single Scenario

Windows:

```powershell
.\build\simulation_runner.exe `
  .\scenarios\base_scenario.json
```

Linux:

```bash
./build/simulation_runner \
    scenarios/base_scenario.json
```

The C++ executable returns a compact JSON result.

---

# Reprocessing Failed Runs

Example:

```bash
python -m factory.reprocess_failed \
    --source-run run_005 \
    --model-version v3 \
    --workers 4
```

The reprocessing system:

* queries failed scenarios from SQLite
* loads the matching scenario files
* evaluates physical feasibility
* reruns simulations
* classifies outcomes
* creates a new run ID
* stores the new results

---

# Extended-Horizon Analysis

Feasible model failures can be tested using a longer horizon:

```bash
python -m factory.test_extended_horizon \
    --source-run run_006 \
    --duration 30
```

This diagnostic was used to establish that all nine feasible 15-second failures converge successfully by 30 seconds.

---

# Feasibility Analysis

A standalone feasibility check is also provided:

```bash
python -m factory.check_feasibility_oracle
```

The oracle uses maximum braking to identify scenarios that cannot physically maintain the configured minimum safety gap.

---

# Failure Analysis

Detailed failure metrics can be inspected using:

```bash
python -m factory.analyze_failures
```

Metrics include:

* failure type
* collision status
* unsafe-gap status
* minimum gap
* minimum TTC
* maximum deceleration
* final gap error
* final relative velocity

---

# Benchmarking

Run workload scaling experiments using:

```bash
python -m factory.benchmark_workloads \
    --counts 100 500 1000 5000 \
    --workers 1 2 4 8 \
    --duration 30 \
    --model-version v3
```

The benchmark measures:

* execution time
* execution throughput
* total process wall time
* speedup
* parallel efficiency

Results are written to:

```text
results/reports/scaling_benchmark.csv
```

---

# Repository Structure

```text
vehicle-simulation-factory/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── analysis/
│   ├── plot_performance.py
│   └── plot_safety_metrics.py
│
├── cpp/
│   ├── CMakeLists.txt
│   │
│   ├── include/
│   │   ├── simulation_runner.hpp
│   │   └── vehicle_model.hpp
│   │
│   └── src/
│       ├── main.cpp
│       ├── simulation_runner.cpp
│       └── vehicle_model.cpp
│
├── factory/
│   ├── __init__.py
│   ├── analyze_failures.py
│   ├── benchmark_scaling.py
│   ├── benchmark_workloads.py
│   ├── check_feasibility_oracle.py
│   ├── database.py
│   ├── feasibility.py
│   ├── generate_scenarios.py
│   ├── reprocess_failed.py
│   ├── run_factory.py
│   ├── summarize_results.py
│   ├── test_extended_horizon.py
│   └── worker.py
│
├── scenarios/
│   ├── base_scenario.json
│   └── generated/
│
├── tests/
│   └── test_factory.py
│
├── results/
│   ├── reports/
│   └── runs/
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── requirements.txt
├── run_factory.ps1
└── README.md
```

---

# Key Engineering Lessons

## A failed simulation is not automatically a model defect

The original validation produced 15 failures.

Further analysis showed:

```text
6 physically infeasible scenarios
9 feasible convergence cases
```

This demonstrates why failure classification matters.

---

## Validation configuration matters

All nine feasible failures at 15 seconds converged successfully at 30 seconds.

Therefore:

```text
simulation horizon
```

was an important part of the validation definition.

Changing the controller unnecessarily could have hidden the real issue.

---

## Physical feasibility should be separated from model performance

A controller should not be penalized for scenarios that are impossible under the vehicle's physical acceleration constraints.

The maximum-braking oracle provides this distinction.

---

## Multiprocessing has practical limits

Increasing the worker count does not provide unlimited scaling.

The benchmark showed throughput saturation at approximately:

```text
23-24 simulations/second
```

for the native local benchmark.

Four workers provided the strongest overall operating point for most tested workloads.

---

## Reproducibility requires more than deterministic models

The project also controls:

* scenario generation
* run IDs
* model versions
* stored configuration
* failure classification
* test execution
* container environment
* CI environment

This allows experiments to be rerun and compared.

---

# Project Highlights

* C++17 vehicle simulation engine
* RK4 vehicle dynamics
* Adaptive Cruise Control
* TTC safety supervision
* deterministic randomized scenario generation
* Python multiprocessing orchestration
* failed-run reprocessing
* SQLite experiment tracking
* model-version comparison
* failure classification
* physical-feasibility oracle
* extended-horizon diagnostics
* automated safety analysis
* 100% feasible-scenario validation pass rate
* performance benchmark up to 5,000 simulations
* worker scaling from 1 to 8 processes
* automated performance visualization
* 18 automated tests
* deterministic simulation testing
* Dockerized Linux execution
* Windows one-command pipeline
* GitHub Actions CI

---

# Example Final Validation

```text
============================================
Simulation Factory Summary
============================================

Total scenarios:          100
Passed:                   94
Model failures:           0
Infeasible scenarios:     6
Errors:                   0

Feasible pass rate:       100.00%
============================================
```

---

# Purpose

This project explores the engineering challenges around vehicle simulation infrastructure rather than only implementing a standalone model.

The focus includes:

* simulation execution
* model validation
* scenario management
* distributed local execution
* failure diagnosis
* result persistence
* regression analysis
* reproducibility
* scalability
* automation

The result is a compact simulation-factory architecture that demonstrates how vehicle-model experiments can be executed and evaluated systematically at scale.

````