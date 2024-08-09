import numpy as np
import pytest

import f3ast


@pytest.fixture
def settings():
    return f3ast.load_settings()


@pytest.fixture
def struct(settings):
    file_path = "examples/spiral.stl"
    struct = f3ast.Structure.from_file(file_path, **settings["structure"])
    return struct


@pytest.fixture
def base_model(struct):
    GR0 = 50e-3  # in um/s, base growth rate
    sigma = 4.4  # in nm, dwell size
    # simple model, without thermal correction
    return f3ast.RRLModel(struct, GR0, sigma)


def test_phi_angle_correction_model(base_model):
    phi0 = np.deg2rad(135)
    correction_factor = 0.1
    angle_correction_model = f3ast.PhiAngleCorrectionModel(
        base_model, phi0, correction_factor
    )
    angle_fun = angle_correction_model.angle_correction_function
    assert angle_fun(phi0) > angle_fun(phi0 + np.pi)
