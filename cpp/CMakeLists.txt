cmake_minimum_required(VERSION 3.20)

project(vehicle_simulation_factory)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

FetchContent_Declare(
    nlohmann_json
    URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

FetchContent_MakeAvailable(
    nlohmann_json
)

add_executable(
    simulation_runner
    src/main.cpp
    src/vehicle_model.cpp
    src/simulation_runner.cpp
)

target_include_directories(
    simulation_runner
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(
    simulation_runner
    PRIVATE
    nlohmann_json::nlohmann_json
)