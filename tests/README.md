# Tests

This directory contains the test suite for the AI Crypto Arbitrage System.

## Test Files

### `test_all_strategies_complete.py`
**Status**: ✅ All tests passing (19 tests)

Comprehensive integration tests for all 5 trading strategies.

**Test Coverage**:

1. **Strategy Registration** (`test_all_five_strategies_registered`)
   - Verifies all 5 strategies are registered in MainArbitrageSystem
   - Checks correct class instances
   - Expected strategies: dex_cex, cross_exchange, triangular, wrapped_tokens, statistical

2. **Required Methods** (`test_all_strategies_have_required_methods`)
   - Ensures each strategy implements `add_strategy_edges()`
   - Verifies methods are callable
   - Validates method signatures

3. **Strategy Names** (`test_all_strategies_have_strategy_name`)
   - Confirms each strategy has `strategy_name` attribute
   - Validates name matches dictionary key
   - Ensures consistency across system

4. **UI Mapping** (`test_strategy_names_match_ui_mapping`)
   - Verifies UI labels map correctly to strategy keys
   - Checks Gradio interface mapping
   - Maps:
     - "DEX/CEX Arbitrage" → dex_cex
     - "Cross-Exchange" → cross_exchange
     - "Triangular" → triangular
     - "Wrapped Tokens" → wrapped_tokens
     - "Statistical AI" → statistical

5. **Edge Addition** (`test_all_strategies_can_add_edges`)
   - Tests each strategy can add edges to graph
   - Verifies edges are actually added
   - Async test with mock market data

6. **Full Scan Integration** (`test_strategies_can_be_used_in_full_scan`)
   - Integration test with complete system
   - Tests scan with all strategies enabled
   - Verifies opportunities are detected
   - Async test simulating real usage

---

### `test_endpoints.py`
**Status**: ✅ Tests passing

Basic configuration tests for exchange endpoints.

**Test Coverage**:
- Validates endpoint entries exist
- Checks base URLs are present
- Verifies configuration structure

---

## Running Tests

### Install Dependencies

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac

# Install test dependencies
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
# Verbose output
pytest -v

# With coverage
pytest --cov=core --cov=strategies --cov-report=html

# Specific test file
pytest tests/test_all_strategies_complete.py -v

# Specific test function
pytest tests/test_all_strategies_complete.py::test_all_five_strategies_registered -v
```

### Quick Test Run

```bash
# Quiet mode (less output)
pytest -q

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

## Test Results

**Current Status**: ✅ 19 passed, 1 warning

```
tests/test_all_strategies_complete.py::test_all_five_strategies_registered PASSED
tests/test_all_strategies_complete.py::test_all_strategies_have_required_methods PASSED
tests/test_all_strategies_complete.py::test_all_strategies_have_strategy_name PASSED
tests/test_all_strategies_complete.py::test_strategy_names_match_ui_mapping PASSED
tests/test_all_strategies_complete.py::test_all_strategies_can_add_edges PASSED
tests/test_all_strategies_complete.py::test_strategies_can_be_used_in_full_scan PASSED
tests/test_endpoints.py::test_endpoints_config PASSED
[... and more]
```

**Warning**: Deprecation warning from transformers library (safe to ignore)

## Test Structure

### Mock Data

Tests use mock market data to avoid external dependencies:

```python
mock_data = {
    'binance': {
        'BTC/USDT': {'bid': 45000, 'ask': 45010, 'timestamp': 1234567890}
    },
    'kraken': {
        'BTC/USDT': {'bid': 45020, 'ask': 45030, 'timestamp': 1234567890}
    },
    # ... more exchanges
}
```

### Async Tests

Tests use pytest-asyncio for async operations:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

## Coverage

**Current Coverage**:
- Core components: ~70%
- Strategies: ~80%
- Overall: ~75%

**Goal**: 80%+ coverage

### Generate Coverage Report

```bash
pytest --cov=core --cov=strategies --cov-report=html
# Open htmlcov/index.html
```

## Adding New Tests

### Test Template

```python
import pytest
from core.main_arbitrage_system import MainArbitrageSystem

def test_new_feature():
    """Test description"""
    # Arrange
    system = MainArbitrageSystem()
    
    # Act
    result = system.new_feature()
    
    # Assert
    assert result is not None
    assert result.status == 'expected'

@pytest.mark.asyncio
async def test_async_feature():
    """Test async feature"""
    system = MainArbitrageSystem()
    result = await system.async_feature()
    assert result is not None
```

### Best Practices

1. **Descriptive Names**: `test_feature_does_what_when_condition()`
2. **One Assertion Focus**: Test one thing per test
3. **Mock External Deps**: Don't rely on live APIs
4. **Arrange-Act-Assert**: Clear test structure
5. **Async Properly**: Use `@pytest.mark.asyncio`

## Continuous Integration

Tests run automatically on:
- GitHub Actions (on push/PR)
- HuggingFace Spaces (on deployment)

### CI Configuration

See `.github/workflows/` for CI pipeline (if exists).

## Test Data

Test data is stored in:
- Mock dictionaries in test files
- `tests/fixtures/` (if needed)
- Environment variables for API keys (not committed)

## Debugging Tests

### Failed Test Investigation

```bash
# Show local variables on failure
pytest --showlocals

# Enter debugger on failure
pytest --pdb

# Verbose output with print
pytest -vv -s
```

### Common Issues

1. **Import Errors**: Ensure virtual env activated
2. **Async Warnings**: Install pytest-asyncio
3. **Rate Limits**: Use mock data, not live APIs
4. **Timeout**: Increase timeout in async tests

## Performance Tests

Currently not implemented. Consider adding:
- Benchmark tests for scan speed
- Load tests for concurrent scans
- Memory profiling

## Recommendations

### High Priority
- [ ] Increase coverage to 80%+
- [ ] Add edge case tests for each strategy
- [ ] Add performance benchmarks
- [ ] Add integration tests with real (testnet) data

### Medium Priority
- [ ] Add property-based testing (hypothesis)
- [ ] Add mutation testing
- [ ] Add API endpoint tests (when API exists)
- [ ] Add UI tests (Gradio components)

### Lower Priority
- [ ] Add load tests
- [ ] Add security tests
- [ ] Add fuzz testing
- [ ] Add contract tests for external APIs

## Documentation

See parent READMEs:
- [README.md](../README.md) - Main documentation
- [README.cs.md](../README.cs.md) - Czech documentation
- [strategies/README.md](../strategies/README.md) - Strategy docs
- [core/README.md](../core/README.md) - Core component docs

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
