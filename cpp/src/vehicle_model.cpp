#include "vehicle_model.hpp"

VehicleModel::VehicleModel(
    double initialPosition,
    double initialVelocity
)
    : state_{
        initialPosition,
        initialVelocity
    } {
}

VehicleState VehicleModel::getState() const {
    return state_;
}

void VehicleModel::stepRK4(
    double acceleration,
    double dt
) {
    const double x0 =
        state_.position;

    const double v0 =
        state_.velocity;

    const double k1x =
        v0;

    const double k1v =
        acceleration;

    const double k2x =
        v0
        +
        0.5
        *
        dt
        *
        k1v;

    const double k2v =
        acceleration;

    const double k3x =
        v0
        +
        0.5
        *
        dt
        *
        k2v;

    const double k3v =
        acceleration;

    const double k4x =
        v0
        +
        dt
        *
        k3v;

    const double k4v =
        acceleration;

    state_.position =
        x0
        +
        dt
        /
        6.0
        *
        (
            k1x
            +
            2.0
            *
            k2x
            +
            2.0
            *
            k3x
            +
            k4x
        );

    state_.velocity =
        v0
        +
        dt
        /
        6.0
        *
        (
            k1v
            +
            2.0
            *
            k2v
            +
            2.0
            *
            k3v
            +
            k4v
        );

    if (
        state_.velocity
        <
        0.0
    ) {
        state_.velocity =
            0.0;
    }
}