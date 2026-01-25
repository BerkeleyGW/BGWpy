# BGWpy Test Suite

## Overview

The BGWpy test suite uses pytest's session-scoped fixtures defined in `conftest.py` to eliminate redundant expensive calculations while maintaining test independence.

## Test Categories

- **Unit tests**: Mock executables to test Python logic quickly
- **Integration tests**: Use real executables / IO to test interactions
- **E2E tests**: Use real executables to validate complete workflows

## Running Tests

### Local Development

```bash
# Run only unit tests (instant, no executables needed)
pytest BGWpy/tests/unit/

# Run unit + integration tests (may need kgrid.x, but still fast)
pytest BGWpy/tests/unit/ BGWpy/tests/integration/

# Skip tests that need missing executables
pytest BGWpy/tests/ -m "not e2e"
```

### On the Cluster (full validation)

```bash
# Run all tests (including expensive E2E tests)
pytest BGWpy/tests/

# Run everything except flow tests (which are slightly redundant)
pytest BGWpy/tests/ -m "not flow"

# Run everything except Abinit tests
pytest BGWpy/tests/ -m "not abinit"

# Use a different filesystem for temp files (avoids Lustre HDF5 issues)
pytest BGWpy/tests/ --tmpdir-base=$SCRATCH/tmp
```

### Run Specific Tests

```bash
# Run a specific test file
pytest BGWpy/tests/integration/test_kgrid_integration.py

# Run a specific test class
pytest BGWpy/tests/test_BGW_tasks.py::TestBGWTasks

# Run a specific test method (only runs needed fixtures)
pytest BGWpy/tests/test_BGW_tasks.py::TestBGWTasks::test_epsilon -v
```

## Test Markers

Tests are marked with pytest markers to enable selective execution:

- `@pytest.mark.unit` - Fast tests, no external executables needed (< 1s total)
- `@pytest.mark.integration` - Tests executable interaction (< 1 min total, needs kgrid.x)
- `@pytest.mark.e2e` - End-to-end tests with complete calculations (mins-hours, needs all executables)
- `@pytest.mark.flow` - Tests flows that compose tasks
- `@pytest.mark.abinit` - Tests that require Abinit installation
