# FEBID 3D Algorithm for Stream File generation (F3AST)

## Installation
Eventually, this should be installable with
```
pip install f3ast
```

For now, install the cloned repository. Navigate with terminal to the folder root directory and run:
```
git clone git@github.com:Skoricius/f3ast.git
pip install -e f3ast --user
```

# Possible issues

This library was tested with Python 3.8.5. Earlier versions of Python might not have all the libraries required to make this project work. To make sure you are using the correct version of Python without affecting your base environment, use conda environments:
```
conda create -n f3ast python=3.8.5
conda activate f3ast
```
And then install the library in the newly created environment.

On MACs, there might be an issue with numba threading. It has something to do with `tbb` library. If someone finds out a fix, please let me know. 
A simple workaround is to comment out line 9 in `slicing.py` which might make the slicing slightly slower.

## Build the documentation
Make sure the project is installed. Also, install [pandoc](https://pandoc.org/installing.html) with `apt install pandoc`. Navigate to `./docs` folder of the cloned directory. In Linux or with Git Bash (on Windows) run:
```
make html
```

If using Windows without Git Bash, first install `make`. Easiest is to open Powershell and install [chocolatey](https://chocolatey.org/install). Then run:
```
choco install make
make html
```

Open `./docs/_build/html/index.html`.

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

For a full step-by-step example, see `examples/building.ipynb`.

For acquiring calibration parameters, see `examples/calibration.ipynb`.

## TO DO
* progressive slicing
* filling in the STL (this should only be done in get_eqd function and should be relatively straightforward)
* Put package on PyPi: https://packaging.python.org/tutorials/packaging-projects/
* https://readthedocs.org for documentation
* improved testing and CI
