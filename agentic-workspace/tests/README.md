# Tests Directory

This directory contains test suites for the agentic workspace.

## Test Structure

```
tests/
├── test_config_loader.py    # Config loader tests
├── test_logger.py            # Logger tests
├── test_agents.py            # Agent tests (to be added)
├── test_workflows.py         # Workflow tests (to be added)
└── test_tools.py             # Tool tests (to be added)
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_config_loader.py
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest --cov=agentic-workspace tests/
```

### Run Specific Test
```bash
pytest tests/test_config_loader.py::TestConfigLoader::test_load_json_success
```

## Writing Tests

### Test Structure

```python
import pytest
from utils.module import Function

class TestFunction:
    """Test cases for Function"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_data = "example"

    def teardown_method(self):
        """Clean up after tests"""
        pass

    def test_basic_functionality(self):
        """Test basic function behavior"""
        result = Function(self.test_data)
        assert result == expected_value

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            Function(invalid_data)
```

### Test Categories

**Unit Tests**
- Test individual functions and classes
- Mock external dependencies
- Fast execution
- High coverage

**Integration Tests**
- Test component interactions
- Use real dependencies where appropriate
- Test workflows end-to-end
- Validate integrations

**Functional Tests**
- Test complete user scenarios
- Test from user perspective
- Validate business requirements

## Test Coverage

### Current Coverage

- `config_loader.py`: Unit tests implemented
- `logger.py`: Unit tests implemented
- Other modules: To be implemented

### Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths
- All error paths tested
- Edge cases covered

### Generating Coverage Report

```bash
# Generate coverage report
pytest --cov=utils --cov-report=html tests/

# View report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Test Fixtures

### Temporary Files

```python
import tempfile
import os

def test_with_temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = f.name

    try:
        # Use temp_path
        pass
    finally:
        os.unlink(temp_path)
```

### Temporary Directories

```python
import tempfile
import shutil

def test_with_temp_dir():
    temp_dir = tempfile.mkdtemp()
    try:
        # Use temp_dir
        pass
    finally:
        shutil.rmtree(temp_dir)
```

### Pytest Fixtures

```python
@pytest.fixture
def sample_config():
    return {
        "name": "test-agent",
        "version": "1.0.0"
    }

def test_with_fixture(sample_config):
    assert sample_config["name"] == "test-agent"
```

## Mocking

### Mock External APIs

```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('module.external_api') as mock_api:
        mock_api.return_value = "mocked response"
        result = function_that_uses_api()
        assert result == expected_result
```

### Mock File Operations

```python
from unittest.mock import mock_open, patch

def test_file_read():
    mock_data = "file content"
    with patch('builtins.open', mock_open(read_data=mock_data)):
        result = read_file("path")
        assert result == mock_data
```

## Best Practices

1. **Test Organization**
   - One test file per module
   - Group related tests in classes
   - Use descriptive test names

2. **Test Independence**
   - Tests should not depend on each other
   - Use fixtures for setup/teardown
   - Clean up resources

3. **Assertions**
   - Use specific assertions
   - Test one thing per test
   - Include failure messages

4. **Coverage**
   - Test happy paths
   - Test error conditions
   - Test edge cases
   - Test boundary conditions

5. **Maintainability**
   - Keep tests simple
   - Avoid test duplication
   - Document complex tests
   - Refactor when needed

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest --cov=. tests/
```

## Troubleshooting

**Import Errors**
```bash
# Ensure parent directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Module Not Found**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio
```

**Tests Not Discovered**
```bash
# Ensure test files start with 'test_'
# Ensure test functions start with 'test_'
```

## Future Test Coverage

### To Be Implemented

- Agent execution tests
- Workflow orchestration tests
- Tool invocation tests
- Integration tests
- Performance tests
- Security tests

### Test Data

Create test data in `tests/fixtures/`:
- Sample configurations
- Mock responses
- Test files
- Expected outputs

## Contributing Tests

When adding new features:
1. Write tests first (TDD)
2. Ensure tests pass
3. Check coverage
4. Document test cases
5. Update this README if needed
