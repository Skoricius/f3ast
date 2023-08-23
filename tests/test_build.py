import pytest

from f3ast import (
    DDModel,
    HeightCorrectionModel,
    RRLModel,
    Stream,
    StreamBuilder,
    Structure,
    load_settings,
)


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def structure_file():
    return "tests/simple_ramp.stl"


@pytest.fixture
def structure(structure_file, settings):
    return Structure.from_file(structure_file, **settings["structure"])


def test_structure_slicing(structure):
    structure.generate_slices()
    assert structure.is_sliced


@pytest.fixture
def model_parameters():
    return {
        "gr": 0.15,
        "k": 1,
        "sigma": 4.4,
        "doubling_length": 200,
    }


@pytest.fixture
def dd_model(structure, settings, model_parameters):
    return DDModel(
        structure,
        model_parameters["gr"],
        model_parameters["k"],
        model_parameters["sigma"],
        **settings["dd_model"]
    )


@pytest.fixture
def rrl_model(structure, settings, model_parameters):
    return RRLModel(structure, model_parameters["gr"], model_parameters["sigma"])


def test_stream(dd_model, settings):
    stream_builder, _ = StreamBuilder.from_model(dd_model, **settings["stream_builder"])
    strm = stream_builder.get_stream()
    assert isinstance(strm, Stream)


@pytest.fixture
def height_correction_model(structure, settings, model_parameters):
    return HeightCorrectionModel(
        structure,
        model_parameters["gr"],
        model_parameters["sigma"],
        model_parameters["doubling_length"],
    )


def test_height_correction_model(height_correction_model, rrl_model, settings):
    stream_builder, _ = StreamBuilder.from_model(
        height_correction_model, **settings["stream_builder"]
    )
    strm = stream_builder.get_stream()
    rrl_stream_builder, _ = StreamBuilder.from_model(
        rrl_model, **settings["stream_builder"]
    )
    rrl_strm = rrl_stream_builder.get_stream()
    assert isinstance(strm, Stream)
    assert rrl_strm.get_time() < strm.get_time()
