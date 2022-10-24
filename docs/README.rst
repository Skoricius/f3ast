FEBID 3D Algorithm for Stream File generation (F3AST)
=====================================================

|Documentation Status|

If you use f3ast in any work or publication, we kindly ask you to cite:

`Skoric L, Sanz-Hernández D, Meng F, Donnelly C, Merino-Aceituno S,
Fernández-Pacheco A. Layer-by-Layer Growth of Complex-Shaped
Three-Dimensional Nanostructures with Focused Electron Beams. Nano Lett.
2020 Jan
8;20(1):184–91. <https://pubs.acs.org/doi/10.1021/acs.nanolett.9b03565>`__

Installation
------------

The package can be installed with pip:

::

   pip install f3ast

To install the most up-to-date version and get the example notebooks,
clone the repository from github:

::

   git clone git@github.com:Skoricius/f3ast.git
   pip install -e f3ast --user

Documentation
-------------

See `readthedocs <https://f3ast.readthedocs.io/en/latest/>`__ for
detailed documentation and examples.

Possible issues
---------------

This library was tested with Python 3.8.5. Earlier versions of Python
might not have all the libraries required to make this project work. To
make sure you are using the correct version of Python without affecting
your base environment, use conda environments:

::

   conda create -n f3ast python=3.8.5
   conda activate f3ast

And then install the library in the newly created environment.

On MACs, there might be an issue with numba threading. It has something
to do with ``tbb`` library. If someone finds out a fix, please let me
know. A simple workaround is to comment out line 9 in ``slicing.py``
which might make the slicing slightly slower.

Building the documentation
--------------------------

Make sure the project is installed. Also, install
`pandoc <https://pandoc.org/installing.html>`__ with
``apt install pandoc``. Navigate to ``./docs`` folder of the cloned
directory. In Linux or with Git Bash (on Windows) run:

::

   make html

If using Windows without Git Bash, first install ``make``. Easiest is to
open Powershell and install
`chocolatey <https://chocolatey.org/install>`__. Then run:

::

   choco install make
   make html

Open ``./docs/_build/html/index.html``.

Usage
=====

Microscope settings are defined in ``settings.hjson`` file and contain
information about the microscope and basic slicing settings. In the
following example, we load the structure and the settings, define the
deposit model we are using, and build the stream.

.. code:: python

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

For a full step-by-step example, see ``examples/building.ipynb``.

For acquiring calibration parameters, see
``examples/calibration.ipynb``.

TO DO
-----

-  progressive slicing
-  filling in the STL (this should only be done in get_eqd function and
   should be relatively straightforward)
-  improved testing and CI

.. |Documentation Status| image:: https://readthedocs.org/projects/f3ast/badge/?version=latest
   :target: https://f3ast.readthedocs.io/en/latest/?badge=latest
