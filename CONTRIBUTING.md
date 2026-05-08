# Contributing to github-autograder-action

MIT licensed, contributions welcome. The most useful contributions: new evaluator types, support for additional languages beyond Python and JavaScript, and improvements to the report rendering.

## How to Contribute

1. Fork the repository on GitHub.
2. Create a topic branch off `main` (e.g. `feat/typescript-evaluator`).
3. Make your changes, run the local test suite, and verify the Docker build still succeeds.
4. Open a pull request describing the new evaluator or change.

## Development setup

```bash
pip install -e ".[dev,grading]"
```

The action itself runs in a Docker container — see `Dockerfile`. If you're adding a new tool dependency, it needs to be installed there too.

## Code style

```bash
ruff check src/ tests/
```

Note: `tests/fixtures/` contains intentionally-bad code used to test the grader's failure detection. The lint config excludes it.

## Testing

```bash
pytest -v
```

When adding a new evaluator, please add fixture submissions under `tests/fixtures/` covering the passing, partially-passing, and failing cases.

## Docker

```bash
docker build -t github-autograder-test .
```

CI also builds the Docker image on every push — if your change touches `Dockerfile` or any installed dependency, please verify the build works locally first.

## Questions

Open an issue with the `question` label.
