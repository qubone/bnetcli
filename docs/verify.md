# bnetcli Verification Guide

This guide provides reproducible local verification steps for testing bnetcli end-to-end.

## 1) Local unit/lint/type checks

```bash
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-cov ruff mypy ty
ruff check src tests
mypy src/bnetcli
ty src/bnetcli
pytest -q --cov=src --cov-fail-under=80
```

## 2) Integration tests (CLI, config edge cases)

```bash
pytest -q tests/test_integration.py
```

## 3) Build and smoke test packages

```bash
python -m pip install --upgrade pip
python -m pip install build
python -m build
python -m pip install dist/*.whl
bnetcli --help
```

## 4) Pipx smoke installation

```bash
python -m pip install --upgrade pip
python -m pip install pipx
python -m pipx install --force dist/*.whl
bnetcli --help
```

## 5) Simulate Steam setups and run doctor

```bash
mkdir -p ~/.local/share/Steam
mkdir -p ~/.steam/root
bnetcli doctor -v
```

## 6) Cross-Python verification (3.10-3.13)

Use `uv` or `pyenv`:

```bash
uv use 3.10
uv pip install -e .
pytest -q
uv use 3.11
uv pip install -e .
pytest -q
```

## 7) TestPyPI and packaging validation

Upload to TestPyPI with credentials and run install from testpypi.

```bash
python -m pip install twine
python -m twine upload --repository testpypi dist/*
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple bnetcli
```
