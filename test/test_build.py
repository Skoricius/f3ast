import pytest

from f3ast import Structure, load_settings, DDModel, StreamBuilder, Stream


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def structure_file():
    return "test/simple_ramp.stl"


@pytest.fixture
def structure(structure_file, settings):
    return Structure.from_file(
        structure_file, **settings["structure"])


def test_structure_slicing(structure):
    structure.generate_slices()
    assert structure.is_sliced


@pytest.fixture
def model(structure, settings):
    gr = 0.15
    k = 1
    sigma = 4.4
    return DDModel(structure, gr, k, sigma, **settings['dd_model'])


def test_stream(model, settings):
    stream_builder, dwell_solver = StreamBuilder.from_model(
        model, **settings['stream_builder'])
    strm = stream_builder.get_stream()
    assert isinstance(strm, Stream)
