SHELL := /bin/bash

CONDA_ENV ?= $(shell grep '^name:' environment.yml | sed -e 's/^name: //')
CONDA_RUN := conda run -n $(CONDA_ENV)

.PHONY: environment.yml
environment.yml:
	conda env export --name $(CONDA_ENV) --from-history | grep -v '^prefix' > environment.yml
