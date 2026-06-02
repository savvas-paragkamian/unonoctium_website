PIXI   := pixi run
HUGO   := $(PIXI) hugo
PY     := $(PIXI) python

BIB_SRC  := data/publications.bib
BIB_OUT  := data/publications.yaml

.PHONY: dev build pubs container stop clean

## Start local dev server (live reload, drafts visible)
dev:
	$(HUGO) server --buildDrafts --navigateToChanged --port 1313

## Build production site → public/
build: pubs
	$(HUGO) --minify --environment production

## Convert publications.bib → data/publications.yaml
pubs:
	@if [ -f $(BIB_SRC) ]; then \
	  $(PY) scripts/bib2data.py $(BIB_SRC) $(BIB_OUT); \
	else \
	  echo "No $(BIB_SRC) found — skipping publications build"; \
	fi

## Build Podman container image and (re)start it
container: build
	podman build -t unonoctium .
	podman run -d --name unonoctium --replace -p 8080:8080 unonoctium
	@echo "Running at http://localhost:8080"

## Stop and remove the container
stop:
	podman stop unonoctium 2>/dev/null || true
	podman rm   unonoctium 2>/dev/null || true

## Remove Hugo build output
clean:
	rm -rf public resources
