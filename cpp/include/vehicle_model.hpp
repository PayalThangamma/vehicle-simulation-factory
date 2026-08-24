#pragma once

struct VehicleState {
    double position;
    double velocity;
};

class VehicleModel {
public:
    VehicleModel(
        double initialPosition,
        double initialVelocity
    );

    VehicleState getState() const;

    void stepRK4(
        double acceleration,
        double dt
    );

private:
    VehicleState state_;
};