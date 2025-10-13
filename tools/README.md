# Tools

This directory contains helper scripts and utilities for development, debugging, and testing.

## Available Tools

### `verify_endpoints.py`
**Purpose**: Validate exchange API endpoints and connectivity

Verifies that all configured exchange endpoints are accessible and functional.

**Usage**:
```bash
# Windows PowerShell
.\.venv\Scripts\python tools/verify_endpoints.py

# Linux/Mac
python tools/verify_endpoints.py
```

**What it does**:
- Tests CCXT client connections for all CEX exchanges
- Falls back to REST API verification
- Skips endpoints requiring API keys (e.g., CoinMarketCap)
- Respects `prefer_ccxt` flags
- Generates `endpoint_report.json`

**Output**:
- Console: Per-exchange status with colors
- File: `endpoint_report.json` with detailed results

**Example Output**:
```json
{
  "binance": {
    "status": "success",
    "method": "ccxt",
    "response_time": 0.234
  },
  "kraken": {
    "status": "success", 
    "method": "rest",
    "response_time": 0.456
  }
}
```

---

### `run_live_scan.py`
**Purpose**: Command-line arbitrage scanner for quick testing

Runs a complete arbitrage scan from the command line without the UI.

**Usage**:
```bash
python tools/run_live_scan.py
```

**Features**:
- Scans all 5 strategies
- Uses default symbols (BTC/USDT, ETH/USDT, BNB/USDT)
- Minimum profit threshold: 0.5%
- Outputs opportunities to console
- Quick way to test system without Gradio

**Useful for**:
- CI/CD pipelines
- Automated scanning
- Development testing
- Performance benchmarking

---

### `run_demo.py`
**Purpose**: Run system in demo mode with simulated data

Demonstrates the system with guaranteed synthetic opportunities for testing UI and flow.

**Usage**:
```bash
python tools/run_demo.py
```

**Features**:
- Injects synthetic exchange data
- Guaranteed to find opportunities
- Safe for testing (no real trading)
- Shows complete system flow

---

### `diagnose_price_artifacts.py`
**Purpose**: Debug tool for investigating price data issues

Analyzes price data for anomalies, artifacts, or inconsistencies.

**Usage**:
```bash
python tools/diagnose_price_artifacts.py
```

**What it checks**:
- Price outliers (too high/low)
- Timestamp issues
- Missing data points
- Exchange-specific artifacts
- Correlation anomalies

**Output**: `diagnostic_report.json`

---

### `inspect_cycles.py`
**Purpose**: Detailed analysis of detected arbitrage cycles

Inspects and analyzes the structure of detected arbitrage opportunities.

**Usage**:
```bash
python tools/inspect_cycles.py
```

**Features**:
- Visualizes cycle paths
- Calculates detailed profit breakdown
- Shows fee impacts
- Identifies best execution strategies

---

### `strip_nonascii.py`
**Purpose**: Clean text files of non-ASCII characters

Utility for cleaning logs and text files.

**Usage**:
```bash
python tools/strip_nonascii.py <input_file> [output_file]
```

**Features**:
- Removes non-ASCII characters
- Preserves file encoding
- Useful for log processing

---

## Common Workflows

### 1. Quick System Check

```bash
# Check all endpoints
python tools/verify_endpoints.py

# Run a live scan
python tools/run_live_scan.py
```

### 2. Debug Price Issues

```bash
# Diagnose price data
python tools/diagnose_price_artifacts.py

# Inspect detected cycles
python tools/inspect_cycles.py
```

### 3. Demo for Presentation

```bash
# Run with guaranteed opportunities
python tools/run_demo.py
```

### 4. Development Testing

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Test endpoints
python tools/verify_endpoints.py

# Quick scan
python tools/run_live_scan.py

# Check results
cat endpoint_report.json
```

## Creating New Tools

### Tool Template

```python
#!/usr/bin/env python3
"""
Tool Name: Description
Usage: python tools/tool_name.py [args]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.main_arbitrage_system import MainArbitrageSystem
import asyncio

async def main():
    """Main tool logic"""
    system = MainArbitrageSystem()
    
    # Your tool logic here
    print("Tool running...")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### Best Practices

1. **Path Setup**: Add parent dir to sys.path for imports
2. **Async**: Use asyncio for data fetching
3. **Error Handling**: Catch and report errors gracefully
4. **Help Text**: Include usage instructions
5. **Output**: Write results to files or console clearly

## Tool Configuration

Tools use configuration from `utils/config.py`:

- Exchange endpoints
- API keys (from environment)
- Logging settings
- Trading parameters

## Environment Variables

Tools respect these environment variables:

```bash
# Logging
LOG_LEVEL=INFO

# API Keys (optional)
COINMARKETCAP_API_KEY=your_key

# Exchange overrides
EXCHANGE_ENDPOINT_BINANCE_BASE_URL=https://api.binance.com

# Demo mode
DEBUG_DEMO_INJECT_SYNTHETIC=True
```

## Output Files

Tools may generate:
- `endpoint_report.json` - Endpoint verification results
- `diagnostic_report.json` - Price diagnostics
- `scan_results.json` - Scan outputs
- `*.log` - Log files

**Note**: Output files are gitignored. See `.gitignore`.

## CI/CD Integration

Tools can be integrated into CI/CD:

```yaml
# Example GitHub Actions
- name: Verify endpoints
  run: python tools/verify_endpoints.py
  
- name: Run scan test
  run: python tools/run_live_scan.py
```

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Solution: Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**Missing Dependencies**:
```bash
# Solution: Install requirements
pip install -r requirements.txt
```

**API Rate Limits**:
```bash
# Solution: Use demo mode or wait
export DEBUG_DEMO_INJECT_SYNTHETIC=True
```

**Timeout Errors**:
- Check network connectivity
- Verify exchange APIs are up
- Use verify_endpoints.py to diagnose

## Recommendations for New Tools

### High Priority
- [ ] Performance profiler tool
- [ ] Backtest runner script
- [ ] Database migration tool
- [ ] Configuration validator

### Medium Priority
- [ ] Log analyzer
- [ ] Alert sender (email/Telegram)
- [ ] Report generator
- [ ] Strategy backtester

### Lower Priority
- [ ] Exchange fee calculator
- [ ] Profit simulator
- [ ] Risk analyzer
- [ ] Portfolio rebalancer

## Documentation

See parent READMEs:
- [README.md](../README.md) - Main documentation
- [README.cs.md](../README.cs.md) - Czech documentation
- [core/README.md](../core/README.md) - Core components
- [tests/README.md](../tests/README.md) - Testing guide

## Contributing Tools

When adding a new tool:

1. Create the script in `tools/`
2. Add docstring with usage
3. Update this README
4. Add to .gitignore if it generates files
5. Test in both Windows and Linux (if possible)
6. Document any environment variables needed
