# FEBID 3D Algorithm for Stream File generation (F3AST)

## Installation
Eventually, this should be installable with
```
pip install f3ast
```

For now, install from requirements:
```
pip install -r requirements
```

# Usage
Microscope settings are defined in `settings.hjson` file and contain information about the microscope and basic slicing settings.
In the following example, we load the structure and the settings, define the deposit model we are using, and build the stream.

```python
# load the settings
settings = load_settings()
# get the structure from a file
struct = Structure.from_file('testing/FunktyBall.stl', **settings["structure"])
struct.rescale(2) # make the structure a bit bigger
# define the model
gr = 0.1
k = 1
sigma = 4
model = DDModel(struct, gr, k, sigma, **settings['dd_model'])

# Solve for dwells and build the stream
stream_builder, dwell_solver = StreamBuilder.from_model(model, **settings['stream_builder'])
dwell_solver.print_total_time()
# save the streamfile and the build information
save_path = 'funky_ball'
strm = stream_builder.get_stream()
strm.write(save_path)
save_build(save_path, dwell_solver, stream_builder)
```

For a full step-by-step example, see `BuildStructure.ipynb`.

For acquiring calibration parameters, see `CalibrationAnalysis.ipynb`.

# Comparison with MATLAB software
* resistance scale is defined differently as MATLAB's `resistance_scale/single_pixel_width`


## TO DO
* progressive slicing
* filling in the STL (this should only be done in get_eqd function and should be relatively straightforward)
* check the possible issue with slicing of the last and first node being connected when they are not supposed to
* Check that single sheet structures are working well
* Change how you define the resistance in parallel in the thesis (resistance scale and layers)
* Put package on PyPi: https://packaging.python.org/tutorials/packaging-projects/
* DO I have the correct normalization in the resistance model (line 50 in resistance.py)