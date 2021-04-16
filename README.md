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



## TO DO
* progressive slicing
* check the possible issue with slicing of the last and first node being connected when they are not supposed to
* Change how you define the resistance in parallel in the thesis
* Check that the resistance is calculated well by comparing with MATLAB (single pixel, branches etc.)
* Check that you get similar deposition times as in MATLAB
* Check that single sheet structures are working well