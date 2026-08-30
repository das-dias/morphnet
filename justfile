# list available recipes
default:
    @just --list

# setup dev-environment
dev:
    uv venv --python 3.12 --clear
    uv sync --all-extras --all-groups --upgrade

# bump version
bump version="patch":
    uvx --python 3.12 --from 'bver-cli==0.1.6' bver bump "{{ version }}"

# compile protobuf schemas to python
proto:
    mkdir -p src/hubnet/hubnet_schema
    protoc \
      --proto_path=protos \
      --python_out=src/hubnet/hubnet_schema \
      --pyi_out=src/hubnet/hubnet_schema \
      protos/*.proto
    # protoc generates bare imports for cross-proto deps; rewrite to fully-qualified
    find src/hubnet/hubnet_schema -name '*_pb2.py' -exec \
      sed -i '' 's/^import \([a-z_]*_pb2\)/import hubnet.hubnet_schema.\1/' {} +
    touch src/hubnet/hubnet_schema/__init__.py

# build package (compiles protos first)
build: proto
    uv build

# run all tests
test:
    uv run pytest

# python linting
lint:
    uv run ruff check --fix .

# format code
fmt:
    uv run ruff format .

# check formatting
fmt-check:
    uv run ruff format --check .

# python type checking
ty:
    uv run ty check .

# generate static images for docs (run manually, commit results)
docs-images:
    uv run python scripts/generate_doc_images.py

# build documentation site
docs:
    uv run mkdocs build --strict

# serve documentation locally with live reload
docs-serve:
    uv run mkdocs serve

# clean generated docs
docs-clean:
    rm -rf site

# clean build artifacts and generated proto files
clean:
    rm -rf build dist *.egg-info src/gflvs/schema
