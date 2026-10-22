SHELL := /bin/bash

CONDA_ENV ?= $(shell grep '^name:' environment.yml | sed -e 's/^name: //')
CONDA_RUN := conda run -n $(CONDA_ENV)

.PHONY: environment.yml
environment.yml:
	conda env export --name $(CONDA_ENV) --from-history | grep -v '^prefix' > environment.yml

# ========================================================================
# Serve docs locally
# ========================================================================
.PHONY: dev-docs-serve dev-docs-shell

# Serve docs/ locally via the real GitHub Pages (Jekyll) pipeline,
# with live reload on save. Bundled gems are cached in .bundle-cache
# so repeat runs are fast and work offline after the first install.
# - starefossen/github-pages does NOT have bash (only sh)
dev-docs-serve:
	rm -f Gemfile.lock
	docker run --rm -it \
		-v "$(PWD)":/srv/jekyll \
		-v "$(PWD)/.bundle-cache":/usr/local/bundle \
		-w /srv/jekyll \
		-p 4000:4000 -p 35729:35729 \
		jekyll/jekyll:latest \
		sh -c "bundle install && bundle exec jekyll serve --source docs --livereload --host 0.0.0.0"

# Drop into a shell in the same container for debugging (e.g. bundle errors)
dev-docs-shell:
	docker run --rm -it \
		--platform linux/amd64 \
		-v "$(PWD)":/srv/jekyll \
		-v "$(PWD)/.bundle-cache":/usr/local/bundle \
		-w /srv/jekyll \
		jekyll/jekyll:latest \
		sh

# END
