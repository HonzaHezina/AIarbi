"""
Centralized constants for the AI Arbitrage System.
This module contains shared constants used across multiple modules to ensure consistency.
"""

# Rate and weight validation thresholds
# Used for validating price rates and graph weights to detect invalid or extreme values
MAX_RATE_THRESHOLD = 1e6  # Maximum allowed rate (rates above this are considered invalid)
MIN_RATE_THRESHOLD = 1e-6  # Minimum allowed rate (rates below this are considered invalid)
MAX_WEIGHT_THRESHOLD = 10  # Maximum allowed absolute weight value in log-space

# Small epsilon value for numerical stability
EPS = 1e-8  # Small epsilon to avoid division by zero and handle floating-point comparison
