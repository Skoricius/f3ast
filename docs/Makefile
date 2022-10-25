# Makefile for Sphinx documentation

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXGEN     ?= sphinx-apidoc
NBCONVERT     ?= jupyter
PYTHON        ?= python
PIP           ?= pip
SOURCEDIR     = .
BUILDDIR      = _build
TEMPLATESDIR  = templates
STATICDIR     = _static

example_notebooks := $(wildcard ../examples/*.ipynb)
example_names = $(foreach path, $(example_notebooks), $(basename $(notdir $(path))))
example_nbs = $(foreach name, $(example_names), examples/$(name).ipynb)

html: conf.py index.rst install.rst examples.rst README.rst f3ast.rst $(example_nbs) .deps
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	touch "$(BUILDDIR)/html/.nojekyll"
	rm -rvf "$(BUILDDIR)/html/_static/examples/*"

.deps: requirements.txt
	$(PIP) install -r requirements.txt
	$(PIP) freeze > .deps

README.rst: ../README.md .deps
	pandoc --from=gfm --to=rst --output=README.rst ../README.md

$(STATICDIR)/examples/%.html: ../examples/%.ipynb .deps
	python -c "import os; os.makedirs('_static/examples', exist_ok=True)"
	$(NBCONVERT) nbconvert --to html --output $(abspath $@) $<

examples/%.ipynb: ../examples/%.ipynb .deps
	python -c "import os; os.makedirs('./examples', exist_ok=True)"
	cp $< $(abspath $@)

f3ast.rst: .deps
	$(SPHINXGEN) -eTf -t "$(TEMPLATESDIR)" -o "$(SOURCEDIR)" ../f3ast

clean:
	rm -rvf "$(BUILDDIR)" "$(STATICDIR)/examples" examples.*.rst trimesh*.rst .deps README.rst

# # All other Sphinx builders
#%: conf.py index.rst install.rst examples.rst README.rst trimesh.rst $(example_rsts) $(example_htmls)
#	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
#
#.PHONY: %